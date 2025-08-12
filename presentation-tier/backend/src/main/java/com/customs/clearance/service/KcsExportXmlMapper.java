package com.customs.clearance.service;

import com.customs.clearance.entity.Declaration;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.w3c.dom.*;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class KcsExportXmlMapper {

    private static final String TEMPLATE_CP = "kcs/KCS_DeclarationOfEXP_830SchemaModule_1.0_standard.xml";
    private static final String NS_WCO = "urn:kr:gov:kcs:data:standard:KCS_DeclarationOfEXP_830SchemaModule:1:0";
    private static final String NS_KCS = "urn:kr:gov:kcs:data:standard:KCS_DeclarationOfEXP_830SchemaModule:1:0";

    private final ObjectMapper om = new ObjectMapper();
    private final Map<String, List<String>> orderMap = new HashMap<>();

    /** 수출 XML 생성 (byte[]) */
    public byte[] buildExportXml(Declaration declaration) throws Exception {
        // 0) 템플릿 로드 → 원래 순서/태그/주석 보존 스냅샷 → 값만 공란화
        Document doc = loadTemplate();
        orderMap.clear();
        snapshotOrder(doc.getDocumentElement(), "/");
        wipeTemplateValues(doc.getDocumentElement());

        // 1) 입력 파싱
        Map<String, Object> root = om.readValue(
                declaration.getDeclarationDetails(), new TypeReference<Map<String, Object>>() {});

        // 상단 공통
        String 신고구분    = S(root.get("신고구분"));           // 예: "H" 또는 "미기재"
        String 거래구분    = S(root.get("거래구분"));           // 예: "11"
        String 종류       = S(root.get("종류"));               // 예: "1"
        String 목적국Raw   = S(root.get("목적국"));             // "GREECE, GR"
        String 선박명      = S(root.get("선박명"));             // "EMIRATES ASANTE"
        String 운송형태     = S(root.get("운송형태"));           // "10FC" → 10 / FC
        String 송품장부호    = S(root.get("송품장부호"));         // "72-103039"
        String 원산지Raw    = S(root.get("원산지"));             // "KRABY" 또는 "KR, A, Y, B, 01"
        String 총중량Raw     = S(root.get("총중량"));            // "441KG"
        String 총포장개수    = S(root.get("총포장개수"));         // "81"
        String 결제금액Raw    = S(root.get("결제금액"));          // "CIFUSD2400.54"

        // 수출대행자 / 제조자 / 구매자
        Party 수출대행자 = parseExporterParty(S(root.get("수출대행자"))); // 상호, 주소/우편, 대표자, 구분코드 추출
        Manufacturer 제조자 = parseManufacturer(S(root.get("제조자")));   // 상호, 통관고유부호/일련/우편/산단
        String 구매자명 = S(root.get("구매자"));

        // 품목
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items =
                (List<Map<String, Object>>) root.getOrDefault("품목별_결과", Collections.emptyList());

        // 2) 헤더/상단
        Element decl = doc.getDocumentElement();

        // 총란수
        setText(ensureChildOrdered(doc, decl, "wco:GoodsItemQuantity"), String.valueOf(items.size()));

        // 거래구분
        setText(ensureChildOrdered(doc, decl, "wco:TransactionNatureCode"), 거래구분);

        // 결제금액: 인도조건/통화/금액 파싱 → 무역조건/인보이스금액
        Payment pay = parseExportPayment(결제금액Raw);
        setText(ensureChildOrdered(doc, decl, "wco:InvoiceAmount"), pay.amount);

        // 총중량(단위)
        TotalWeight tw = parseTotalWeight(총중량Raw);
        Element tgm = ensureChildOrdered(doc, decl, "wco:TotalGrossMassMeasure");
        setText(tgm, tw.value);
        setAttrAllowEmpty(tgm, NS_KCS, "kcs:UnitCode", tw.unit); // KG 등

        // 총포장갯수
        setText(ensureChildOrdered(doc, decl, "wco:TotalPackageQuantity"), nzBlankIfMissing(총포장개수));

        // CustomsProcedure: 신고구분/종류 (미기재면 공란 유지)
        Element cp = ensureChildOrdered(doc, decl, "wco:CustomsProcedure");
        setText(ensureChildOrdered(doc, cp, "kcs:ProcessTypeCode"), 신고구분);
        setText(ensureChildOrdered(doc, cp, "kcs:TypeCode"), 종류);

        // 전단 운송수단: 선박명
        Element btm = ensureChildOrdered(doc, decl, "wco:BorderTransportMeans");
        setText(ensureChildOrdered(doc, btm, "wco:Name"), 선박명);

        // 3) Exporter / Agent / Manufacturer
        // Agent (수출대행자 상호)
        Element agent = ensureChildOrdered(doc, decl, "wco:Agent");
        setText(ensureChildOrdered(doc, agent, "wco:Name"), 수출대행자.name);

        // Exporter (수출화주)
        Element exporter = ensureChildOrdered(doc, decl, "wco:Exporter");
        // IDs 유지(공란), 상호/구분/주소/대표자만 채움
        setText(ensureChildOrdered(doc, exporter, "wco:Name"), 수출대행자.name);
        setText(ensureChildOrdered(doc, exporter, "wco:RoleCode"), ""); // 사업자등록번호구분부호: 입력 없으면 공란
        setText(ensureChildOrdered(doc, exporter, "kcs:TypeCode"), 수출대행자.typeCode); // 수출자구분(A/B/…)
        Element expAddr = ensureChildOrdered(doc, exporter, "wco:Address");
        setText(ensureChildOrdered(doc, expAddr, "wco:CountrySubDivisionID"), ""); // 도로명코드: 없음
        setText(ensureChildOrdered(doc, expAddr, "wco:Line"), 수출대행자.address);
        setText(ensureChildOrdered(doc, expAddr, "wco:PostcodeID"), 수출대행자.postcode);
        setText(ensureChildOrdered(doc, expAddr, "kcs:BuildingNumber"), "");
        setText(ensureChildOrdered(doc, expAddr, "kcs:Description"), 수출대행자.address);
        Element expContact = ensureChildOrdered(doc, exporter, "wco:Contact");
        setText(ensureChildOrdered(doc, expContact, "kcs:RepresentativeName"), 수출대행자.representative);

        // Manufacturer
        Element man = ensureChildOrdered(doc, decl, "wco:Manufacturer");
        // 통관고유부호/일련은 템플릿 태그 유지(공란)
        setText(ensureChildOrdered(doc, man, "wco:Name"), 제조자.name);
        Element manAddr = ensureChildOrdered(doc, man, "wco:Address");
        setText(ensureChildOrdered(doc, manAddr, "wco:PostcodeID"), 제조자.postcode);

        // 4) GoodsShipment 블록
        Element gs = ensureChildOrdered(doc, decl, "wco:GoodsShipment");

        // Buyer
        Element buyer = ensureChildOrdered(doc, gs, "wco:Buyer");
        setText(ensureChildOrdered(doc, buyer, "wco:Name"), 구매자명);
        Element bAddr = ensureChildOrdered(doc, buyer, "wco:Address");
        setText(ensureChildOrdered(doc, bAddr, "wco:CountryCode"), parseCountryCode(목적국Raw)); // "GREECE, GR" → "GR"

        // AdditionalDocument: L/C 번호(공란 유지) + 송품장부호 추가(별도 문서칸)
        Element ad1 = ensureChildOrdered(doc, gs, "wco:AdditionalDocument");
        setText(ensureChildOrdered(doc, ad1, "wco:ID"), ""); // L/C 번호는 입력 없으면 공란

        Element inv = ensureChildOrdered(doc, gs, "wco:Invoice");
        setText(ensureChildOrdered(doc, inv, "wco:ID"), 송품장부호);


        // Consignment: 운송형태(운송수단/운송용기)
        TransportMode tm = parseTransportMode(운송형태);
        Element cons = ensureChildOrdered(doc, gs, "wco:Consignment");
        Element consBtm = ensureChildOrdered(doc, cons, "wco:BorderTransportMeans");
        setText(ensureChildOrdered(doc, consBtm, "wco:TypeCode"), tm.modeCode);
        Element teq = ensureChildOrdered(doc, consBtm, "wco:TransportEquipment");
        setText(ensureChildOrdered(doc, teq, "wco:CharacteristicCode"), tm.containerCode);

        // GoodsLocation: 물품소재지(우편/주소) 입력 없으면 공란 유지
        Element gl = ensureChildOrdered(doc, cons, "wco:GoodsLocation");
        setText(ensureChildOrdered(doc, gl, "wco:ID"), ""); // 우편번호
        Element glAddr = ensureChildOrdered(doc, gl, "wco:Address");
        setText(ensureChildOrdered(doc, glAddr, "kcs:Description"), ""); // 주소

        // CustomsValuation: 운임/보험료(입력 없으면 공란)
        Element val = ensureChildOrdered(doc, gs, "wco:CustomsValuation");
        setText(ensureChildOrdered(doc, val, "wco:ExitToEntryChargeAmount"), ""); // 보험료
        setText(ensureChildOrdered(doc, val, "wco:FreightChargeAmount"), "");     // 운임

        // TradeTerms: 인도조건/결제방법
        Element tt = ensureChildOrdered(doc, gs, "wco:TradeTerms");
        setText(ensureChildOrdered(doc, tt, "wco:ConditionCode"), pay.incoterm);
        setText(ensureChildOrdered(doc, tt, "kcs:SettlementConditionCode"), pay.method);

        // Warehouse: 장치장소명 공란 유지
        setText(ensureChildOrdered(doc, gs, "wco:Warehouse").getElementsByTagNameNS(NS_WCO,"Name").getLength()==0
                ? ensureChildOrdered(doc, ensureChildOrdered(doc, gs, "wco:Warehouse"), "wco:Name")
                : ensureChildOrdered(doc, gs, "wco:Warehouse").getElementsByTagNameNS(NS_WCO,"Name").item(0)
                instanceof Element ? (Element) ensureChildOrdered(doc, gs, "wco:Warehouse").getElementsByTagNameNS(NS_WCO,"Name").item(0)
                : ensureChildOrdered(doc, ensureChildOrdered(doc, gs, "wco:Warehouse"), "wco:Name")
                , "");

        // 5) 품목(기존 GovernmentAgencyGoodsItem 제거 후 재작성)
        removeDirectChildren(gs, NS_WCO, "GovernmentAgencyGoodsItem");
        ExportOrigin xo = parseExportOrigin(원산지Raw);

        for (int i = 0; i < items.size(); i++) {
            Map<String, Object> it = items.get(i);

            String 품명     = S(it.get("품명"));
            String 거래품명  = S(it.get("거래품명"));
            String 상표명    = S(it.get("상표명"));
            String 규격     = S(it.get("모델및규격"));
            String 수량     = S(it.get("수량"));
            String 단가     = S(it.get("단가"));
            String 금액     = S(it.get("금액")); // "21.31000 (USD)"
            String 세번부호  = normalizeHs10(S(it.get("세번부호"))); // "4981150000" 형태로
            String 순중량   = onlyNumber(S(it.get("순중량")));      // "275.00"
            String 포장개수  = S(it.get("포장개수"));

            Element gag = createChildOrdered(doc, gs, "wco:GovernmentAgencyGoodsItem");
            setText(ensureChildOrdered(doc, gag, "wco:SequenceNumeric"), String.valueOf(i + 1));

            Element cmd = ensureChildOrdered(doc, gag, "wco:Commodity");
            // 거래품명을 CargoDescription으로
            setText(ensureChildOrdered(doc, cmd, "wco:CargoDescription"), 거래품명);
            // HS
            Element cls = ensureChildOrdered(doc, cmd, "wco:Classification");
            setText(ensureChildOrdered(doc, cls, "wco:ID"), 세번부호);
            // 수량
            Element cq = ensureChildOrdered(doc, cmd, "wco:CountQuantity");
            setText(cq, nzBlankIfMissing(수량));
            setAttrAllowEmpty(cq, NS_KCS, "kcs:UnitCode", ""); // 단위 정보 없으면 공란
            // 상세(모델/단가/금액/상표명 보강: 모델에 상표/품명 포함해서 가독)
            Element det = ensureChildOrdered(doc, cmd, "wco:DetailedCommodity");
            setText(ensureChildOrdered(doc, det, "wco:Description"),
                    joinNonEmpty(" ; ",
                            nzBlankIfMissing(규격),
                            nzBlankIfMissing(상표명.equalsIgnoreCase("NO") ? "" : "BRAND:"+상표명),
                            nzBlankIfMissing(품명.equalsIgnoreCase("NO") ? "" : "NAME:"+품명)
                    ));
            setText(ensureChildOrdered(doc, det, "wco:UnitPriceAmount"), cleanNum(단가));
            setText(ensureChildOrdered(doc, det, "wco:ValueAmount"), cleanNum(firstNumber(금액)));

            // 순중량
            Element gm = ensureChildOrdered(doc, gag, "wco:GoodsMeasure");
            Element nnw = ensureChildOrdered(doc, gm, "wco:NetNetWeightMeasure");
            setText(nnw, nzBlankIfMissing(순중량));
            setAttrAllowEmpty(nnw, NS_KCS, "kcs:UnitCode", isBlank(순중량) ? "" : "KG");

            // 포장개수
            if (!isBlank(포장개수)) {
                Element pkg = ensureChildOrdered(doc, gag, "wco:Packaging");
                setText(ensureChildOrdered(doc, pkg, "wco:QuantityQuantity"), 포장개수);
                // 포장종류코드는 항목 입력 없으면 생략(공란)
            }

            // 원산지 (수출: 국가부호 + 선택적으로 결정기준/표시/FTA/협정명)
            Element ori = ensureChildOrdered(doc, gag, "wco:Origin");
            setText(ensureChildOrdered(doc, ori, "wco:CountryCode"), xo.country);
            // 스키마 허용 시 아래 3줄 유지, 아니면 공란 그대로 둠
            Element rule = ensureChildOrdered(doc, ori, "wco:RuleCode");
            setText(rule, xo.rule);
            Element od = ensureChildOrdered(doc, ori, "wco:OriginDescription");
            setText(ensureChildOrdered(doc, od, "kcs:DisplayIndicatorCode"), xo.display);
            setText(ensureChildOrdered(doc, od, "kcs:FTAIssuanceIndicatorCode"), xo.ftaIssue);
            setText(ensureChildOrdered(doc, od, "kcs:AgreementNameCode"), xo.agreement);
        }

        // 6) 직렬화
        return toBytes(doc);
    }

    // ---------- Template & Order ----------
    private Document loadTemplate() throws Exception {
        DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
        f.setNamespaceAware(true);
        try (InputStream in = new ClassPathResource(TEMPLATE_CP).getInputStream()) {
            return f.newDocumentBuilder().parse(in);
        }
    }
    private void snapshotOrder(Element parent, String path) {
        List<String> order = new ArrayList<>();
        NodeList nl = parent.getChildNodes();
        for (int i=0;i<nl.getLength();i++){
            Node n = nl.item(i);
            if (n.getNodeType()==Node.ELEMENT_NODE) order.add(qname((Element)n));
        }
        String me = pathOf(parent, path);
        orderMap.put(me, order);
        for (int i=0;i<nl.getLength();i++){
            Node n = nl.item(i);
            if (n.getNodeType()==Node.ELEMENT_NODE) snapshotOrder((Element)n, me);
        }
    }
    private String pathOf(Element el, String parentPath){ return (parentPath.endsWith("/")? parentPath: parentPath+"/") + qname(el); }
    private String qname(Element el){ String p=el.getPrefix(); return (p==null||p.isEmpty())? el.getLocalName() : p+":"+el.getLocalName(); }

    private Element ensureChildOrdered(Document d, Element parent, String qn){
        NodeList nl = parent.getChildNodes();
        for (int i=0;i<nl.getLength();i++){
            Node n = nl.item(i);
            if (n.getNodeType()==Node.ELEMENT_NODE && qn.equals(qname((Element)n))) return (Element)n;
        }
        Element el = d.createElementNS(qn.startsWith("kcs:")? NS_KCS : NS_WCO, qn);
        insertInOrder(parent, el);
        return el;
    }
    private Element createChildOrdered(Document d, Element parent, String qn){
        Element el = d.createElementNS(qn.startsWith("kcs:")? NS_KCS : NS_WCO, qn);
        insertInOrder(parent, el);
        return el;
    }
    private void insertInOrder(Element parent, Element el){
        String parentPath = pathOf(parent, "/");
        List<String> order = orderMap.getOrDefault(parentPath, Collections.emptyList());
        String name = qname(el);
        int targetIdx = indexIn(order, name);
        NodeList nl = parent.getChildNodes();
        for (int i=0;i<nl.getLength();i++){
            Node n = nl.item(i);
            if (n.getNodeType()!=Node.ELEMENT_NODE) continue;
            int sibIdx = indexIn(order, qname((Element)n));
            if (sibIdx>=0 && (targetIdx<0 || targetIdx < sibIdx)){
                parent.insertBefore(el, n); return;
            }
        }
        parent.appendChild(el);
    }
    private int indexIn(List<String> order, String name){ for (int i=0;i<order.size();i++) if (order.get(i).equals(name)) return i; return -1; }

    // ---------- Wipe: 값/속성 공란화 (태그/주석/순서 보존) ----------
    private void wipeTemplateValues(Element el) {
        // 속성 초기화(네임스페이스/스키마 제외)
        NamedNodeMap attrs = el.getAttributes();
        for (int i = 0; i < attrs.getLength(); i++) {
            Node a = attrs.item(i);
            String name = a.getNodeName();
            if (name.startsWith("xmlns")) continue;
            if ("xsi:schemaLocation".equals(name)) continue;
            a.setNodeValue("");
        }
        boolean hasElementChild = false;
        NodeList nl = el.getChildNodes();
        for (int i = 0; i < nl.getLength(); i++) {
            if (nl.item(i).getNodeType() == Node.ELEMENT_NODE) { hasElementChild = true; break; }
        }
        if (!hasElementChild) el.setTextContent(""); // 리프 텍스트만 공란
        for (int i = 0; i < nl.getLength(); i++) {
            Node n = nl.item(i);
            if (n.getNodeType() == Node.ELEMENT_NODE) wipeTemplateValues((Element) n);
        }
    }

    // ---------- Setters / Utils ----------
    private void setText(Element el, String value){ el.setTextContent(isBlank(value) ? "" : value); }
    private void setAttrAllowEmpty(Element el, String ns, String qn, String value){
        if (ns==null) el.setAttribute(qn, isBlank(value) ? "" : value);
        else el.setAttributeNS(ns, qn, isBlank(value) ? "" : value);
    }
    private void removeDirectChildren(Element parent, String ns, String local){
        NodeList nl = parent.getChildNodes();
        for (int i = nl.getLength()-1; i>=0; i--){
            Node c = nl.item(i);
            if (c.getNodeType()==Node.ELEMENT_NODE
                    && ns.equals(c.getNamespaceURI())
                    && local.equals(c.getLocalName())){
                parent.removeChild(c);
            }
        }
    }
    private byte[] toBytes(Document doc) throws Exception {
        var tf = TransformerFactory.newInstance().newTransformer();
        tf.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
        tf.setOutputProperty(OutputKeys.INDENT, "yes");
        tf.setOutputProperty("{http://xml.apache.org/xslt}indent-amount", "2");
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        tf.transform(new DOMSource(doc), new StreamResult(baos));
        return baos.toByteArray();
    }

    private static String S(Object o){ return o==null? "" : String.valueOf(o).trim(); }
    private static boolean isBlank(String s){
        if (s == null) return true;
        String t = s.trim();
        if (t.isEmpty()) return true;
        String norm = t.replaceAll("[\\s·\\-_/]", "").toLowerCase();
        return "미기재".equals(t) || "미기재".equals(norm) || "migijae".equals(norm) || "-".equals(t);
    }
    private static String nzBlankIfMissing(String s){ return isBlank(s) ? "" : s.trim(); }
    private static String cleanNum(String s){ return isBlank(s)? "" : s.replaceAll("[,\\s]", ""); }
    private static String firstNumber(String s){
        if (isBlank(s)) return "";
        Matcher m = Pattern.compile("([0-9]+(?:\\.[0-9]+)?)").matcher(s);
        return m.find()? m.group(1) : "";
    }
    private static String onlyNumber(String s){ return firstNumber(s); }
    private static String joinNonEmpty(String sep, String... vals){
        List<String> out = new ArrayList<>();
        for (String v: vals) if (!isBlank(v)) out.add(v.trim());
        return String.join(sep, out);
    }
    private static String normalizeHs10(String s){
        if (isBlank(s)) return "";
        String t = s.replaceAll("[^0-9]", "");
        if (t.length() == 10) return t;
        if (t.length() == 6)  return t + "0000";
        return t; // 있는 그대로(검증은 외부에서)
    }
    private static String parseCountryCode(String raw){
        if (isBlank(raw)) return "";
        // "GREECE, GR" → "GR"
        Matcher m = Pattern.compile("\\b([A-Za-z]{2})\\b").matcher(raw);
        String last = "";
        while (m.find()) last = m.group(1);
        return last.toUpperCase(Locale.ROOT);
    }

    // 결제금액: "CIFUSD2400.54" / "CIF, USD, 2400.54, TT" 등
    private Payment parseExportPayment(String raw){
        if (isBlank(raw)) return new Payment("","","","");
        String s = raw.replaceAll("[,\\s]", "");
        // 패턴1: ^([A-Z]{3})([A-Z]{3})([0-9.]+)([A-Z]{0,2})?$
        Matcher m = Pattern.compile("^([A-Z]{3})([A-Z]{3})([0-9.]+)([A-Z]{0,2})?$").matcher(s);
        if (m.matches()){
            return new Payment(m.group(1), m.group(2), m.group(3), nzBlankIfMissing(m.group(4)));
        }
        // 패턴2: CSV
        List<String> parts = new ArrayList<>();
        for (String p : raw.split(",")) if (!isBlank(p)) parts.add(p.trim());
        String ic = parts.size()>=1? parts.get(0) : "";
        String cc = parts.size()>=2? parts.get(1) : "";
        String am = parts.size()>=3? cleanNum(parts.get(2)) : "";
        String md = parts.size()>=4? parts.get(3) : "";
        return new Payment(ic, cc, am, md);
    }
    private static class Payment { final String incoterm, amount, method;
        Payment(String i,String c,String a,String m){incoterm=i;amount=a;method=m;} }

    private static class TotalWeight { final String value, unit;
        TotalWeight(String v,String u){value=v;unit=u;} }
    private TotalWeight parseTotalWeight(String raw){
        String v = firstNumber(raw);
        String u = "";
        Matcher m = Pattern.compile("([A-Za-z]{2,3})$").matcher(raw == null ? "" : raw.trim());
        if (m.find()) u = m.group(1).toUpperCase(Locale.ROOT);
        return new TotalWeight(nzBlankIfMissing(v), nzBlankIfMissing(u));
    }

    private static class TransportMode { final String modeCode, containerCode;
        TransportMode(String m, String c){modeCode=m;containerCode=c;} }
    private TransportMode parseTransportMode(String raw){
        if (isBlank(raw)) return new TransportMode("","");
        // "10FC" → "10" / "FC"
        Matcher m = Pattern.compile("^([0-9]{1,2})([A-Za-z]{2,3})?$").matcher(raw.trim());
        if (m.matches()){
            return new TransportMode(nzBlankIfMissing(m.group(1)), nzBlankIfMissing(m.group(2)));
        }
        // "10, FC" 등
        String[] a = raw.split(",");
        String mode = a.length>0 ? a[0].trim() : "";
        String cont = a.length>1 ? a[1].trim() : "";
        return new TransportMode(nzBlankIfMissing(mode), nzBlankIfMissing(cont));
    }

    // 수출대행자: "상호, 주소..., 우편, 대표자, (기타), 수출자구분?" 등 자유형
    private static class Party {
        final String name, address, postcode, representative, typeCode;
        Party(String n,String a,String p,String r,String t){name=n;address=a;postcode=p;representative=r;typeCode=t;}
    }
    private Party parseExporterParty(String raw){
        if (isBlank(raw)) return new Party("","","","","");
        String s = raw;
        // 대표자(한글/영문) 후보: 콤마 구분 중 2~5번째쯤 위치하는 경우 많음
        String representative = "";
        String postcode = "";
        // 우편번호 5자리
        Matcher pm = Pattern.compile("\\b(\\d{5})\\b").matcher(s);
        if (pm.find()) postcode = pm.group(1);
        // 대표자: 한글/영문 이름 2~10자
        Matcher rm = Pattern.compile("([가-힣A-Za-z\\-\\s]{2,10})").matcher(s);
        while (rm.find()){
            String cand = rm.group(1).trim();
            if (!cand.isEmpty() && !cand.matches("(?i)MOTEC|TECHNOLOGY|CO\\.?|LTD\\.?|MI|GICHAE|MIGIJAE"))
                representative = cand; // 가장 나중 후보 채택
        }
        // 상호: 앞쪽 첫 콤마 전
        String name = s.split(",")[0].trim();
        // 주소: 상호 제외 나머지에서 우편/대표자/미기재 제거
        String addr = s.replaceFirst(Pattern.quote(name)+",?\\s*", "")
                .replace(postcode, "")
                .replace(representative, "")
                .replace("미기재","")
                .replaceAll("\\s{2,}", " ")
                .replaceAll("(^,\\s*|,\\s*$)","")
                .trim();
        // 수출자구분 코드 추정(A/B/C/D) 한 글자
        Matcher tm = Pattern.compile("\\b([A-D])\\b").matcher(raw);
        String type = tm.find()? tm.group(1) : "";
        return new Party(nzBlankIfMissing(name), nzBlankIfMissing(addr), nzBlankIfMissing(postcode), nzBlankIfMissing(representative), nzBlankIfMissing(type));
    }

    // 제조자: "상호, 통관고유부호(또는 미상), 일련번호, 우편, 산업단지부호"
    private static class Manufacturer {
        final String name, postcode;
        Manufacturer(String n,String c,String s,String p,String i){name=n;postcode=p;}
    }
    // "상호, 미상, 0000, 51312, 미상" 같은 자유형을 안전 파싱
    private Manufacturer parseManufacturer(String raw){
        if (isBlank(raw)) return new Manufacturer("","","","","");
        String[] tok = Arrays.stream(raw.split(","))
                .map(String::trim)
                .toArray(String[]::new);

        String name = tok.length>0? tok[0] : "";

        String code = "";
        String serial = "";
        String postcode = "";
        String ind = "";

        for (int i=1;i<tok.length;i++){
            String t = tok[i];
            if (t.equals("미상") || isBlank(t)) continue;
            if (postcode.isEmpty() && t.matches("^\\d{5}$")) { postcode = t; continue; } // 5자리=우편번호
            if (serial.isEmpty() && t.matches("^\\d{1,10}$")) { serial = t; continue; }  // 숫자=일련번호
            if (code.isEmpty() && t.matches("^[A-Za-z0-9\\-]{3,}$")) { code = t; continue; }
            if (ind.isEmpty()) ind = t;
        }
        return new Manufacturer(nzBlankIfMissing(name), nzBlankIfMissing(code),
                nzBlankIfMissing(serial), nzBlankIfMissing(postcode), nzBlankIfMissing(ind));
    }


    // 수출 원산지: "KRABY" → KR/A/B/Y/""  |  "KR, A, Y, B, 01"
    private static class ExportOrigin { final String country, rule, display, ftaIssue, agreement;
        ExportOrigin(String c,String r,String d,String f,String a){country=c;rule=r;display=d;ftaIssue=f;agreement=a;} }
    private ExportOrigin parseExportOrigin(String raw){
        if (isBlank(raw)) return new ExportOrigin("","","","","");
        String s = raw.trim();
        if (s.matches("^[A-Za-z]{2}[A-Za-z]{3}$")) {
            // KRABY → KR / A / B / Y / ""
            String c = s.substring(0,2).toUpperCase(Locale.ROOT);
            String r = String.valueOf(s.charAt(2)).toUpperCase(Locale.ROOT);
            String d = String.valueOf(s.charAt(3)).toUpperCase(Locale.ROOT);
            String f = String.valueOf(s.charAt(4)).toUpperCase(Locale.ROOT);
            return new ExportOrigin(c,r,d,f,"");
        }
        String[] a = Arrays.stream(s.split(",")).map(String::trim).toArray(String[]::new);
        String c = a.length>0? a[0] : "";
        String r = a.length>1? a[1] : "";
        String d = a.length>2? a[2] : "";
        String f = a.length>3? a[3] : "";
        String g = a.length>4? a[4] : "";
        return new ExportOrigin(nzBlankIfMissing(c), nzBlankIfMissing(r), nzBlankIfMissing(d), nzBlankIfMissing(f), nzBlankIfMissing(g));
    }
}
