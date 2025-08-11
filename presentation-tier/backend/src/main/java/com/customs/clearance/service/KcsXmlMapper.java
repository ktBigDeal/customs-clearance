package com.customs.clearance.service;

import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.w3c.dom.*;

import javax.xml.namespace.NamespaceContext;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.xpath.*;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.*;

/**
 * KcsXmlMapper - 다품목 + 빈항목 자동제거(prune) + 콤마규칙 파싱 + Agent/Exporter 규칙 + 운송용기부호 + 원산지 객체 지원
 *
 * 규칙 요약:
 *  - "미기재/미상/-/NA" 등은 공란으로 간주 → 노드 미생성(최종 prune에서 제거)
 *  - 회사명 파싱 시 숫자/주소 느낌 토큰이 나오기 전까지는 전부 상호로 누적 → "Co., Ltd."가 상호에 붙음
 *  - Agent(수출대행자): 상호만 출력
 *  - Exporter(수출화주): 상호 + kcs:TypeCode + Address(Line/PostcodeID/kcs:Description) + Contact/kcs:RepresentativeName
 *  - Exporter 정보가 없고 Agent만 있으면 → Exporter=Agent 정보로 채우고 kcs:TypeCode="A"
 *  - 운송형태 "10FC" → TypeCode="10", TransportEquipment/CharacteristicCode="FC"
 *  - 원산지: 문자열("KRABY") 또는 객체({국가부호/결정기준/표시여부/FTA원산지증명서발급여부/발급협정명}) 모두 지원
 */
@Service
public class KcsXmlMapper {

    private static final String IMP_PATH = "kcs/KCS_DeclarationOfIMP_929SchemaModule_1.0_standard.xml";
    private static final String EXP_PATH = "kcs/KCS_DeclarationOfEXP_830SchemaModule_1.0_standard.xml";

    // ----------------------------------------------------------------------
    // Public API
    // ----------------------------------------------------------------------

    public byte[] buildExportXml(Map<String, Object> details) throws Exception {
        Document doc = loadTemplate(EXP_PATH);
        Map<String, String> ns = nsFrom(doc);
        XPath xp = newXPath(ns);
        keep.clear();

        // 헤더/합계
        setTotalsExport(doc, xp, details);

        // 운송수단/운송형태 (TypeCode + CharacteristicCode)
        upsertTransport(doc, xp, ns, details);

        // HBL/MBL
        upsertBLs(doc, xp, ns, details);

        // 목적국
        setDestinationCountry(doc, xp, details);

        // Buyer / Agent / Exporter
        setBuyerInfo(doc, xp, ns, details);
        setAgentExporterWithRules(doc, xp, ns, details);

        // 다품목
        Element gs = ensureGoodsShipmentIfNeeded(doc, xp, ns);
        List<Map<String, Object>> items = getItems(details);
        if (!items.isEmpty()) {
            setKeep(node(xp, doc, "wco:Declaration/wco:GoodsItemQuantity"), String.valueOf(items.size()));
            removeDirectChildren(gs, ns.get("wco"), "GovernmentAgencyGoodsItem");
            for (int i = 0; i < items.size(); i++) {
                addItem(doc, xp, ns, gs, items.get(i), i + 1, details);
            }
            markKeep(gs);
        }

        pruneUnkept(doc.getDocumentElement());
        return toBytes(doc);
    }

    public byte[] buildImportXml(Map<String, Object> details) throws Exception {
        Document doc = loadTemplate(IMP_PATH);
        Map<String, String> ns = nsFrom(doc);
        XPath xp = newXPath(ns);
        keep.clear();

        setTotalsImport(doc, xp, details);

        upsertTransport(doc, xp, ns, details);
        upsertBLs(doc, xp, ns, details);

        // 필요 시 수입에도 동일 규칙 적용
        setBuyerInfo(doc, xp, ns, details);
        setAgentExporterWithRules(doc, xp, ns, details);

        Element gs = ensureGoodsShipmentIfNeeded(doc, xp, ns);
        List<Map<String, Object>> items = getItems(details);
        if (!items.isEmpty()) {
            setKeep(node(xp, doc, "wco:Declaration/wco:GoodsItemQuantity"), String.valueOf(items.size()));
            removeDirectChildren(gs, ns.get("wco"), "GovernmentAgencyGoodsItem");
            for (int i = 0; i < items.size(); i++) {
                addItem(doc, xp, ns, gs, items.get(i), i + 1, details);
            }
            markKeep(gs);
        }

        pruneUnkept(doc.getDocumentElement());
        return toBytes(doc);
    }

    // ----------------------------------------------------------------------
    // Core mapping
    // ----------------------------------------------------------------------

    private void setTotalsExport(Document doc, XPath xp, Map<String, Object> details) {
        setKeep(node(xp, doc, "wco:Declaration/wco:InvoiceAmount"),
                onlyNum(v(details, "결제금액", "invoice_amount", "total_amount")));
        setKeep(node(xp, doc, "wco:Declaration/wco:TotalGrossMassMeasure"),
                onlyNum(v(details, "총중량", "gross_weight")));
        setKeep(node(xp, doc, "wco:Declaration/wco:TotalPackageQuantity"),
                onlyNum(v(details, "총포장개수", "total_packages")));
        setKeep(node(xp, doc, "wco:Declaration/wco:TransactionNatureCode"),
                v(details, "거래구분", "transaction_nature"));
    }

    private void setTotalsImport(Document doc, XPath xp, Map<String, Object> details) {
        setKeep(node(xp, doc, "wco:Declaration/wco:InvoiceAmount"),
                onlyNum(v(details, "결제금액", "invoice_amount", "total_amount")));
        setKeep(node(xp, doc, "wco:Declaration/wco:TotalGrossMassMeasure"),
                onlyNum(v(details, "총중량", "gross_weight")));
        setKeep(node(xp, doc, "wco:Declaration/wco:TotalPackageQuantity"),
                onlyNum(v(details, "총포장개수", "total_packages")));
    }

    private void upsertTransport(Document doc, XPath xp, Map<String, String> ns, Map<String, Object> details) {
        String vessel = v(details, "선기명", "선박명", "vessel_name");
        String nat    = v(details, "선박국적", "선기국적", "vessel_nationality");

        if (!isBlank(vessel) || !isBlank(nat)) {
            Element border = ensureElement(doc, node(xp, doc, "wco:Declaration/wco:BorderTransportMeans"),
                    ns.get("wco"), "wco:BorderTransportMeans", doc.getDocumentElement());
            setKeep(node(xp, border, "wco:Name"), vessel);
            setKeep(node(xp, border, "wco:RegistrationNationalityID"), nat);
            markKeep(border);
        }

        // 운송형태 예: "10FC" → TypeCode="10", 운송용기부호(Characteristics) = "FC"
        String tm = v(details, "운송형태", "transport_mode");
        if (!isBlank(tm)) {
            String typeCode = tm.replaceAll("\\D", "");       // 숫자만
            String contCode = tm.replaceAll("[^A-Za-z]", ""); // 문자만
            Element gs = ensureGoodsShipmentIfNeeded(doc, xp, ns);
            Element cons = ensureChild(doc, gs, ns.get("wco"), "wco:Consignment");
            Element innerBtm = ensureChild(doc, cons, ns.get("wco"), "wco:BorderTransportMeans");
            if (!isBlank(typeCode)) {
                Element type = ensureChild(doc, innerBtm, ns.get("wco"), "wco:TypeCode");
                setKeep(type, typeCode);
            }
            if (!isBlank(contCode)) {
                Element te = ensureChild(doc, innerBtm, ns.get("wco"), "wco:TransportEquipment");
                Element ch = ensureChild(doc, te, ns.get("wco"), "wco:CharacteristicCode");
                setKeep(ch, contCode); // 운송용기 부호
                markKeep(te);
            }
            markKeep(innerBtm); markKeep(cons); markKeep(gs);
        }
    }

    private void upsertBLs(Document doc, XPath xp, Map<String, String> ns, Map<String, Object> details) {
        String hbl = v(details, "BL_AWB번호", "BL_AWB_번호", "bl_number", "HBL");
        String mbl = v(details, "Master_BL_번호", "mbl_number", "MBL");
        if (isBlank(hbl) && isBlank(mbl)) return;

        Element gs = ensureGoodsShipmentIfNeeded(doc, xp, ns);
        Element cons = ensureChild(doc, gs, ns.get("wco"), "wco:Consignment");
        if (!isBlank(hbl)) upsertTcd(doc, xp, cons, ns, hbl, "714");
        if (!isBlank(mbl)) upsertTcd(doc, xp, cons, ns, mbl, "704");
        markKeep(cons); markKeep(gs);
    }

    private void setDestinationCountry(Document doc, XPath xp, Map<String, Object> details) {
        String dest = v(details, "목적국", "destination_country"); // "GREECE, GR"
        if (isBlank(dest)) return;
        String code = dest.contains(",") ? dest.substring(dest.lastIndexOf(",") + 1).trim() : dest;
        setKeep(node(xp, doc, "wco:Declaration/wco:GoodsShipment/wco:Buyer/wco:Address/wco:CountryCode"), code);
    }

    private void addItem(Document doc, XPath xp, Map<String, String> ns,
                         Element goodsShipment, Map<String, Object> item, int seq,
                         Map<String,Object> headerDetails) {
        Element gag = doc.createElementNS(ns.get("wco"), "wco:GovernmentAgencyGoodsItem");
        goodsShipment.appendChild(gag);
        markKeep(gag);

        createChildKeep(doc, gag, ns.get("wco"), "wco:SequenceNumeric", String.valueOf(seq));

        Element commodity = ensureChild(doc, gag, ns.get("wco"), "wco:Commodity");
        markKeep(commodity);

        String name  = v(item, "거래품명", "품명", "item_name");
        String model = v(item, "모델및규격", "모델 및 규격", "model_spec");
        createChildKeep(doc, commodity, ns.get("wco"), "wco:CargoDescription", firstNonNull(name, model));

        String hs = hs10(v(item, "세번번호", "세번부호", "hs_code"));
        if (!isBlank(hs)) {
            Element classification = ensureChild(doc, commodity, ns.get("wco"), "wco:Classification");
            markKeep(classification);
            createChildKeep(doc, classification, ns.get("wco"), "wco:ID", hs);
        }

        String qty = onlyNum(v(item, "수량", "quantity"));
        if (!isBlank(qty)) {
            Element countQ = doc.createElementNS(ns.get("wco"), "wco:CountQuantity");
            countQ.setAttributeNS(ns.get("kcs"), "kcs:UnitCode", "EA");
            countQ.setTextContent(qty.trim());
            commodity.appendChild(countQ);
            markKeep(countQ);
        }

        String unitPrice = onlyNum(v(item, "단가", "unit_price"));
        String valueAmt  = onlyNum(v(item, "금액", "amount"));
        boolean anyDetail = !isBlank(model) || !isBlank(unitPrice) || !isBlank(valueAmt);
        if (anyDetail) {
            Element det = ensureChild(doc, commodity, ns.get("wco"), "wco:DetailedCommodity");
            markKeep(det);
            createChildKeep(doc, det, ns.get("wco"), "wco:Description", model);
            createChildKeep(doc, det, ns.get("wco"), "wco:UnitPriceAmount", unitPrice);
            createChildKeep(doc, det, ns.get("wco"), "wco:ValueAmount", valueAmt);
        }

        String net = onlyNum(v(item, "순중량", "net_weight"));
        if (!isBlank(net)) {
            Element gm  = ensureChild(doc, gag, ns.get("wco"), "wco:GoodsMeasure");
            markKeep(gm);
            Element nnw = doc.createElementNS(ns.get("wco"), "wco:NetNetWeightMeasure");
            nnw.setAttributeNS(ns.get("kcs"), "kcs:UnitCode", "KG");
            nnw.setTextContent(net.trim());
            gm.appendChild(nnw);
            markKeep(nnw);
        }

        String pkg = onlyNum(v(item, "포장개수", "포장 개수", "packages"));
        if (!isBlank(pkg)) {
            Element packaging = ensureChild(doc, gag, ns.get("wco"), "wco:Packaging");
            markKeep(packaging);
            createChildKeep(doc, packaging, ns.get("wco"), "wco:QuantityQuantity", pkg);
            createChildKeep(doc, packaging, ns.get("wco"), "wco:TypeCode", "CT");
        }

        // --- 원산지 (아이템 우선, 없으면 헤더 상속)
        Object originObj = item.get("원산지");
        if (originObj == null) originObj = headerDetails.get("원산지");

        String originCode = null, rule = null, disp = null, fta = null, agr = null;

        if (originObj instanceof String str) {
            OriginParts op = parsePackedOriginString(str);
            originCode = op.country;
            if (rule == null) rule = op.rule;
            if (disp == null) disp = op.disp;
            if (fta  == null) fta  = op.fta;
            if (agr  == null) agr  = op.agr; // 있으면 사용
        } else if (originObj instanceof Map<?,?> om) {
            originCode = toIso2Country(nestedString(om.get("국가부호")));
            if (originCode == null) originCode = toIso2Country(nestedString(om.get("country")));

            rule = oneCharCode(nestedString(om.get("결정기준")));
            if (rule == null) rule = oneCharCode(nestedString(om.get("rule")));

            disp = oneCharCode(nestedString(om.get("표시여부")));
            if (disp == null) disp = oneCharCode(nestedString(om.get("display")));

            fta = oneCharCode(nestedString(om.get("FTA원산지증명서발급여부")));
            if (fta == null) fta = oneCharCode(nestedString(om.get("fta_issue")));

            agr = nestedString(om.get("발급협정명"));
            if (agr == null) agr = nestedString(om.get("agreement"));
        }

        if (!isBlank(originCode) || !isBlank(rule) || !isBlank(disp) || !isBlank(fta) || !isBlank(agr)) {
            Element originEl = ensureChild(doc, gag, ns.get("wco"), "wco:Origin");
            markKeep(originEl);
            if (!isBlank(originCode)) createChildKeep(doc, originEl, ns.get("wco"), "wco:CountryCode", originCode);
            if (!isBlank(rule))       createChildKeep(doc, originEl, ns.get("wco"), "wco:RuleCode", rule);

            if (!isBlank(disp) || !isBlank(fta) || !isBlank(agr)) {
                Element od = ensureChild(doc, originEl, ns.get("wco"), "wco:OriginDescription");
                markKeep(od);
                if (!isBlank(disp)) createChildKeep(doc, od, ns.get("kcs"), "kcs:DisplayIndicatorCode", disp);
                if (!isBlank(fta))  createChildKeep(doc, od, ns.get("kcs"), "kcs:FTAIssuanceIndicatorCode", fta);
                if (!isBlank(agr))  createChildKeep(doc, od, ns.get("kcs"), "kcs:AgreementNameCode", agr);
            }
        }
    }

    // ----------------------------------------------------------------------
    // Buyer / Agent / Exporter (규칙 반영)
    // ----------------------------------------------------------------------

    // Buyer (구매자): 구조화 키 우선, 없으면 콤마규칙 파싱
    private void setBuyerInfo(Document doc, XPath xp, Map<String,String> ns, Map<String,Object> details) {
        String buyerName = v(details, "구매자_회사명", "구매자상호", "buyer_name");
        String buyerAddr = v(details, "구매자_주소", "buyer_address");
        String buyerZip  = v(details, "구매자_우편번호", "buyer_postcode", "buyer_zip");

        if (isBlank(buyerName) && isBlank(buyerAddr) && isBlank(buyerZip)) {
            Party p = parsePartyByComma(v(details, "구매자", "buyer"));
            if (p != null) {
                buyerName = p.company;
                buyerAddr = p.address;
                buyerZip  = p.postcode;
            }
        }
        if (isBlank(buyerName) && isBlank(buyerAddr) && isBlank(buyerZip)) return;

        Element gs = ensureGoodsShipmentIfNeeded(doc, xp, ns);
        Element buyer = ensureChild(doc, gs, ns.get("wco"), "wco:Buyer");
        markKeep(buyer); markKeep(gs);

        if (!isBlank(buyerName)) setKeep(ensureChild(doc, buyer, ns.get("wco"), "wco:Name"), buyerName);
        if (!isBlank(buyerAddr) || !isBlank(buyerZip)) {
            Element addr = ensureChild(doc, buyer, ns.get("wco"), "wco:Address");
            markKeep(addr);
            if (!isBlank(buyerAddr)) createChildKeep(doc, addr, ns.get("wco"), "wco:Line", buyerAddr);
            if (!isBlank(buyerZip))  createChildKeep(doc, addr, ns.get("wco"), "wco:PostcodeID", buyerZip);
        }
    }

    /**
     * Agent/Exporter 규칙:
     *  - Agent: 상호만 출력
     *  - Exporter: 상호 + kcs:TypeCode + Address(Line/Zip/kcs:Description) + Contact/kcs:RepresentativeName
     *  - Exporter 정보가 없고 Agent만 있으면 → Exporter=Agent 정보로 채우고 TypeCode="A"
     *  - 입력의 "수출자_구분"(exporter_type_code)이 있으면 그 값을 우선, 없고 Agent만 있으면 "A"
     */
    private void setAgentExporterWithRules(Document doc, XPath xp, Map<String,String> ns, Map<String,Object> details) {
        // Agent 원문과 파싱
        String agentRaw  = v(details, "수출대행자", "agent", "forwarder");
        Party  ap        = parsePartyByComma(agentRaw);
        String agentName = v(details, "수출대행자_회사명", "agent_name");
        if (isBlank(agentName) && ap != null) agentName = ap.company;

        // Agent: 상호만 출력
        if (!isBlank(agentName)) {
            Element agent = ensureChild(doc, doc.getDocumentElement(), ns.get("wco"), "wco:Agent");
            markKeep(agent);
            setKeep(ensureChild(doc, agent, ns.get("wco"), "wco:Name"), agentName);
        }

        // Exporter 입력
        String expName = v(details, "수출자_회사명", "수출화주", "수출자", "exporter_name");
        String expAddrDetail = v(details, "수출화주상세주소", "exporter_address_detail");
        String expAddrDesc   = v(details, "수출화주주소", "exporter_address"); // kcs:Description
        String expZip        = v(details, "수출자_우편번호", "수출화주_우편번호", "exporter_postcode", "exporter_zip");
        String expRep        = v(details, "수출자_대표자명", "exporter_rep_name");
        String expTypeInput  = v(details, "수출자_구분", "exporter_type_code");

        // 단일 문자열만 있는 경우 콤마 파싱
        if (isBlank(expName) && isBlank(expAddrDetail) && isBlank(expAddrDesc) && isBlank(expZip)) {
            Party ep = parsePartyByComma(v(details, "수출자", "exporter"));
            if (ep != null) {
                expName = firstNonNull(expName, ep.company);
                if (isBlank(expAddrDetail)) expAddrDetail = ep.address;
                if (isBlank(expAddrDesc))   expAddrDesc   = ep.address;
                if (isBlank(expZip))        expZip        = ep.postcode;
                if (isBlank(expRep))        expRep        = ep.person;
            }
        }

        // Exporter 비어 있고 Agent만 있으면 → Agent 정보로 채움 + TypeCode=A
        boolean exporterEmpty = isBlank(expName) && isBlank(expAddrDetail) && isBlank(expAddrDesc) && isBlank(expZip) && isBlank(expRep);
        if (exporterEmpty && (ap != null || !isBlank(agentName))) {
            expName = firstNonNull(expName, agentName);
            if (ap != null) {
                if (isBlank(expAddrDetail)) expAddrDetail = ap.address;
                if (isBlank(expAddrDesc))   expAddrDesc   = ap.address;
                if (isBlank(expZip))        expZip        = ap.postcode;
                if (isBlank(expRep))        expRep        = ap.person;
            }
            if (isBlank(expTypeInput)) expTypeInput = "A";
        }

        // Exporter 출력
        if (!isBlank(expName) || !isBlank(expAddrDetail) || !isBlank(expAddrDesc) || !isBlank(expZip) || !isBlank(expRep) || !isBlank(expTypeInput)) {
            Element exporter = ensureChild(doc, doc.getDocumentElement(), ns.get("wco"), "wco:Exporter");
            markKeep(exporter);

            if (!isBlank(expName)) setKeep(ensureChild(doc, exporter, ns.get("wco"), "wco:Name"), expName);
            if (!isBlank(expTypeInput)) createChildKeep(doc, exporter, ns.get("kcs"), "kcs:TypeCode", expTypeInput);

            if (!isBlank(expAddrDetail) || !isBlank(expZip) || !isBlank(expAddrDesc)) {
                Element addr = ensureChild(doc, exporter, ns.get("wco"), "wco:Address");
                markKeep(addr);
                if (!isBlank(expAddrDetail)) createChildKeep(doc, addr, ns.get("wco"), "wco:Line", expAddrDetail);
                if (!isBlank(expZip))        createChildKeep(doc, addr, ns.get("wco"), "wco:PostcodeID", expZip);
                if (!isBlank(expAddrDesc))   createChildKeep(doc, addr, ns.get("kcs"), "kcs:Description", expAddrDesc);
            }
            if (!isBlank(expRep)) {
                Element contact = ensureChild(doc, exporter, ns.get("wco"), "wco:Contact");
                markKeep(contact);
                createChildKeep(doc, contact, ns.get("kcs"), "kcs:RepresentativeName", expRep);
            }
        }
    }

    // ----------------------------------------------------------------------
    // Keep / Prune
    // ----------------------------------------------------------------------

    private final Set<Node> keep = Collections.newSetFromMap(new IdentityHashMap<>());

    private void markKeep(Node n) {
        while (n != null && n.getNodeType() == Node.ELEMENT_NODE) {
            keep.add(n);
            n = n.getParentNode();
        }
    }

    private void pruneUnkept(Node n) {
        for (Node c = n.getFirstChild(); c != null; ) {
            Node next = c.getNextSibling();
            if (c.getNodeType() == Node.ELEMENT_NODE) pruneUnkept(c);
            c = next;
        }
        if (!keep.contains(n) && n.getParentNode() != null && n.getNodeType() == Node.ELEMENT_NODE) {
            n.getParentNode().removeChild(n);
        }
    }

    private void setKeep(Node node, String value) {
        String v = blankAsNull(value);
        if (node != null && !isBlank(v)) {
            node.setTextContent(v.trim());
            markKeep(node);
        }
    }

    private Element createChildKeep(Document d, Node parent, String ns, String qname, String value) {
        String v = blankAsNull(value);
        if (isBlank(v) || parent == null) return null;
        Element el = d.createElementNS(ns, qname);
        el.setTextContent(v.trim());
        parent.appendChild(el);
        markKeep(el);
        return el;
    }

    // ----------------------------------------------------------------------
    // DOM / XPath helpers
    // ----------------------------------------------------------------------

    private static Document loadTemplate(String cp) throws Exception {
        var f = DocumentBuilderFactory.newInstance();
        f.setNamespaceAware(true);
        try (InputStream in = new ClassPathResource(cp).getInputStream()) {
            return f.newDocumentBuilder().parse(in);
        }
    }

    private static Map<String, String> nsFrom(Document doc) {
        String wco = doc.getDocumentElement().getNamespaceURI();
        String kcs = doc.lookupNamespaceURI("kcs");
        if (kcs == null) kcs = wco;
        return Map.of("wco", wco, "kcs", kcs);
    }

    private static XPath newXPath(Map<String, String> ns) {
        XPath xp = XPathFactory.newInstance().newXPath();
        xp.setNamespaceContext(new NamespaceContext() {
            @Override public String getNamespaceURI(String prefix) { return ns.get(prefix); }
            @Override public String getPrefix(String namespaceURI) { return null; }
            @Override public Iterator<String> getPrefixes(String namespaceURI) { return null; }
        });
        return xp;
    }

    private static Node node(XPath xp, Node base, String expr) {
        try { return (Node) xp.evaluate(expr, base, XPathConstants.NODE); }
        catch (Exception e) { return null; }
    }

    private static Element ensureElement(Document d, Node maybe, String ns, String qname, Node parentIfCreate) {
        if (maybe instanceof Element) return (Element) maybe;
        Element el = d.createElementNS(ns, qname);
        parentIfCreate.appendChild(el);
        return el;
    }

    private static Element ensureChild(Document d, Node parent, String ns, String qname) {
        if (!(parent instanceof Element)) return null;
        NodeList nl = ((Element) parent).getElementsByTagNameNS(ns, qname.substring(qname.indexOf(':') + 1));
        if (nl.getLength() > 0) return (Element) nl.item(0);
        Element el = d.createElementNS(ns, qname);
        parent.appendChild(el);
        return el;
    }

    private Element ensureGoodsShipmentIfNeeded(Document doc, XPath xp, Map<String,String> ns) {
        Node n = node(xp, doc, "wco:Declaration/wco:GoodsShipment");
        if (n instanceof Element) return (Element) n;
        Element gs = doc.createElementNS(ns.get("wco"), "wco:GoodsShipment");
        doc.getDocumentElement().appendChild(gs);
        return gs;
    }

    private static void removeDirectChildren(Element parent, String ns, String local) {
        NodeList nl = parent.getChildNodes();
        for (int i = nl.getLength() - 1; i >= 0; i--) {
            Node c = nl.item(i);
            if (c.getNodeType() == Node.ELEMENT_NODE
                    && ns.equals(c.getNamespaceURI())
                    && local.equals(c.getLocalName())) {
                parent.removeChild(c);
            }
        }
    }

    private static byte[] toBytes(Document doc) throws Exception {
        Transformer tf = TransformerFactory.newInstance().newTransformer();
        tf.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
        tf.setOutputProperty(OutputKeys.INDENT, "yes");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        tf.transform(new DOMSource(doc), new StreamResult(out));
        return out.toByteArray();
    }

    // ----------------------------------------------------------------------
    // Value helpers (공란/미기재 처리 포함)
    // ----------------------------------------------------------------------

    private static String getS(Map<String, Object> m, String... keys) {
        for (String k : keys) {
            Object v = m.get(k);
            if (v != null) return String.valueOf(v);
        }
        return null;
    }

    /** 비즈니스 규칙: "미기재" 등은 공란으로 처리 */
    private static String blankAsNull(String s) {
        if (s == null) return null;
        String t = s.trim();
        if (t.isEmpty()) return null;
        String low = t.toLowerCase(Locale.ROOT);
        if (t.equals("미기재") || t.equals("미상") || t.equals("-") || low.equals("na") || low.equals("n/a")) return null;
        return t;
    }

    /** getS + 공란 규칙 적용 */
    private static String v(Map<String,Object> m, String... keys){
        return blankAsNull(getS(m, keys));
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> getItems(Map<String, Object> details) {
        Object v = details.get("품목별_결과");
        if (v instanceof List<?> l && !l.isEmpty() && l.get(0) instanceof Map<?, ?>)
            return (List<Map<String, Object>>) v;
        v = details.get("items");
        if (v instanceof List<?> l2 && !l2.isEmpty() && l2.get(0) instanceof Map<?, ?>)
            return (List<Map<String, Object>>) v;
        return Collections.emptyList();
    }

    private static boolean isBlank(String s) { return s == null || s.trim().isEmpty(); }

    private static String onlyDigits(String s) {
        if (s == null) return null;
        String r = s.replaceAll("\\D", "");
        return r.isEmpty() ? null : r;
    }

    /** "47.44", "33 KG", "9064.67 (USD)" → "47.44", "33", "9064.67" */
    private static String onlyNum(String s) {
        String t = blankAsNull(s);
        if (t == null) return null;
        String[] parts = t.replace(",", "").replaceAll("[^0-9.]", " ").trim().split("\\s+");
        return (parts.length > 0 && !parts[0].isBlank()) ? parts[0] : null;
    }

    /** "4981.15-0000" → "4981150000" (10자리) */
    private static String hs10(String s) {
        String t = blankAsNull(s);
        if (t == null) return null;
        String d = t.replaceAll("\\D", "");
        if (d.length() >= 10) return d.substring(0, 10);
        return d.isEmpty() ? null : d;
    }

    private static String firstNonNull(String a, String b) { return !isBlank(a) ? a : b; }

    // ----------------------------------------------------------------------
    // BL/MBL upsert
    // ----------------------------------------------------------------------

    private void upsertTcd(Document doc, XPath xp, Node cons, Map<String,String> ns,
                           String idVal, String typeCode) {
        String idTxt = blankAsNull(idVal);
        if (idTxt == null || cons == null) return;

        try {
            NodeList list = (NodeList) xp.evaluate("wco:TransportContractDocument", cons, XPathConstants.NODESET);
            for (int i = 0; i < list.getLength(); i++) {
                Node tcd = list.item(i);
                Node tc = node(xp, tcd, "wco:TypeCode");
                if (tc != null && typeCode.equals(tc.getTextContent())) {
                    setKeep(node(xp, tcd, "wco:ID"), idTxt);
                    markKeep(tcd); markKeep(cons);
                    return;
                }
            }
            Element tcd = doc.createElementNS(ns.get("wco"), "wco:TransportContractDocument");
            cons.appendChild(tcd);
            markKeep(tcd); markKeep(cons);
            createChildKeep(doc, tcd, ns.get("wco"), "wco:ID", idTxt);
            createChildKeep(doc, tcd, ns.get("wco"), "wco:TypeCode", typeCode);
        } catch (Exception e) {
            // 필요시 로깅
        }
    }

    // ----------------------------------------------------------------------
    // Origin helpers (문자열/객체 지원)
    // ----------------------------------------------------------------------

    // "KRABY" / "KOREA (KR)" → "KR"
    private static String toIso2Country(String s){
        String t = blankAsNull(s);
        if (t == null) return null;
        String up = t.toUpperCase(Locale.ROOT);
        var m = java.util.regex.Pattern.compile("\\b([A-Z]{2})\\b").matcher(up);
        if (m.find()) return m.group(1);
        String letters = up.replaceAll("[^A-Z]", "");
        return letters.length() >= 2 ? letters.substring(0,2) : null;
    }
    // 원산지 압축문자열 파싱: "KRABY" → KR(국가), A(결정기준), B(표시여부), Y(FTA발급), [남는건 협정명]
    private static class OriginParts {
        String country; String rule; String disp; String fta; String agr;
    }

    private static OriginParts parsePackedOriginString(String s){
        OriginParts op = new OriginParts();
        String t = blankAsNull(s);
        if (t == null) return op;
        // 영숫자만 남김
        String alnum = t.replaceAll("[^A-Za-z0-9]", "");
        if (alnum.length() >= 2 && Character.isLetter(alnum.charAt(0)) && Character.isLetter(alnum.charAt(1))) {
            op.country = ("" + alnum.charAt(0) + alnum.charAt(1)).toUpperCase(Locale.ROOT);
            if (alnum.length() >= 3) op.rule = oneCharCode(String.valueOf(alnum.charAt(2)));    // A/B/C/D/E/2/4/6/8
            if (alnum.length() >= 4) op.disp = oneCharCode(String.valueOf(alnum.charAt(3)));    // Y/N/B/G
            if (alnum.length() >= 5) op.fta  = oneCharCode(String.valueOf(alnum.charAt(4)));    // Y/N
            if (alnum.length() > 5) {
                String rest = alnum.substring(5).trim();
                if (!rest.isEmpty()) op.agr = rest.toUpperCase(Locale.ROOT); // 남은건 협정명으로 취급(옵션)
            }
        } else {
            // 기존 방식으로만 추출
            op.country = toIso2Country(t);
        }
        return op;
    }
    @SuppressWarnings("unchecked")
    private static String nestedString(Object o){
        if (o == null) return null;
        if (o instanceof String s) return blankAsNull(s);
        if (o instanceof Map<?,?> mm) {
            Object v;
            v = mm.get("값");      if (v instanceof String) return blankAsNull((String)v);
            v = mm.get("value");   if (v instanceof String) return blankAsNull((String)v);
            v = mm.get("code");    if (v instanceof String) return blankAsNull((String)v);
            v = mm.get("예시");      if (v instanceof String) return blankAsNull((String)v);
            v = mm.get("example");  if (v instanceof String) return blankAsNull((String)v);
        }
        return null;
    }

    private static String oneCharCode(String s){
        String t = blankAsNull(s);
        if (t == null) return null;
        t = t.trim();
        if (t.length() == 1) return t.toUpperCase(Locale.ROOT);
        return String.valueOf(Character.toUpperCase(t.charAt(0)));
    }

    // ----------------------------------------------------------------------
    // Party comma parsing (".Ltd" 상호 유지, 주소/우편/담당 분리)
    // ----------------------------------------------------------------------

    private static class Party {
        String company;   // 회사명 (Co., Ltd. 포함)
        String address;   // 주소(콤마 포함)
        String postcode;  // 우편번호(숫자만)
        String person;    // 담당자명
    }

    private static String digits(String s){ return s==null? null : s.replaceAll("\\D", ""); }
    private static boolean looksLikeZipTok(String tok){
        String d = digits(tok);
        return d != null && d.length() >= 4 && d.length() <= 6; // KR 5자리 중심
    }
    private static boolean looksLikeAddressTok(String tok){
        if (tok == null) return false;
        if (tok.matches(".*\\d.*")) return true; // 숫자 포함 → 주소 가능성 높음
        String low = tok.toLowerCase(Locale.ROOT);
        return low.contains("street") || low.contains("st.") || low.contains("road") || low.contains("rd.")
                || low.contains("ave") || low.contains("blvd") || low.contains("dong") || low.contains("ro")
                || low.contains("si") || low.contains("shi") || low.contains("gu") || low.contains("gun")
                || low.contains("changwon") || low.contains("gyeongnam");
    }

    /**
     * 콤마 규칙:
     *   회사명 [, 회사명 연장 토큰들(예: Co. / Ltd.) ...] , 주소..., 우편번호 , 담당자명
     * - 숫자/주소스멜 토큰이 나오기 전까지는 회사명에 누적 → "Co., Ltd."가 상호에 유지됨
     * - 마지막-1 토큰이 우편번호로 보이면 [..주소..][zip][담당자]
     */
    private static Party parsePartyByComma(String raw){
    String base = blankAsNull(raw);
    if (base == null) return null;

    String[] toks = base.split(",");
    List<String> parts = new ArrayList<>();
    for (String t : toks) {
        String v = blankAsNull(t);
        if (v != null) parts.add(v);
    }
    if (parts.isEmpty()) return null;

    Party p = new Party();
    List<String> companyParts = new ArrayList<>();
    int n = parts.size();

    // 1) 회사명 누적 (.Ltd 유지)
    companyParts.add(parts.get(0));
    int idx = 1;
    while (idx < n) {
        String tk = parts.get(idx);
        if (looksLikeAddressTok(tk) || looksLikeZipTok(tk)) break;
        companyParts.add(tk);
        idx++;
    }
    p.company = String.join(", ", companyParts).trim();

    // 2) 주소/우편/담당
    if (idx < n) {
        if (n - idx >= 2 && looksLikeZipTok(parts.get(n - 2))) {
            String zipTok = parts.get(n - 2);
            p.postcode = digits(zipTok); // 53216

            // ★ zipTok에서 숫자를 뺀 '문자' 부분(예: "Gyeongnam")을 주소에 보존
            String zipAlpha = zipTok.replaceAll("\\d", "").trim();
            String addrCore = (n - idx - 2 > 0) ? String.join(", ", parts.subList(idx, n - 2)) : "";
            if (!zipAlpha.isEmpty()) {
                p.address = addrCore.isEmpty() ? zipAlpha : addrCore + ", " + zipAlpha;
            } else {
                p.address = addrCore;
            }

            p.person = parts.get(n - 1);
        } else {
            p.address = String.join(", ", parts.subList(idx, n));
        }
    }
    return p;
}

}
