package com.customs.clearance.service;

import com.customs.clearance.entity.Declaration;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.context.annotation.Primary;
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

@Primary
@Service
public class KcsImportXmlMapper {

    private static final String TEMPLATE_CP = "kcs/KCS_DeclarationOfIMP_929SchemaModule_1.0_standard.xml";
    private static final String NS_WCO = "urn:kr:gov:kcs:data:standard:KCS_DeclarationOfIMP_929SchemaModule:1:0";
    private static final String NS_KCS = "urn:kr:gov:kcs:data:standard:KCS_DeclarationOfIMP_929SchemaModule:1:0";

    private final ObjectMapper om = new ObjectMapper();
    private final Map<String, List<String>> orderMap = new HashMap<>();

    public byte[] buildImportXml(Declaration declaration) throws Exception {
        // 0) 템플릿 로드 → 원래 순서 스냅샷 → 전체 공란화 (태그/주석/순서 유지)
        Document doc = loadTemplate();
        orderMap.clear();
        snapshotOrder(doc.getDocumentElement(), "/");
        wipeTemplateValues(doc.getDocumentElement());

        // 1) 입력 파싱
        Map<String, Object> root = om.readValue(
                declaration.getDeclarationDetails(), new TypeReference<Map<String, Object>>() {});

        String 신고구분   = firstToken(S(root.get("신고구분")));   // e.g. "A"
        String 거래구분   = firstToken(S(root.get("거래구분")));   // e.g. "11"
        String 종류       = firstToken(S(root.get("종류")));       // e.g. "11"
        String 원산지Raw  = S(root.get("원산지"));                 // "KR, A, Y, B, 01"
        String blNo       = S(root.get("BL_AWB_번호"));
        String mblNo      = S(root.get("Master_BL_번호"));
        String 국내도착항  = S(root.get("국내도착항"));
        String 선기명      = S(root.get("선기명"));
        String 적출국     = S(root.get("적출국"));

        String 납세의무자Raw = S(root.get("납세의무자"));
        Importer importerIn  = parseImporterStrict(S(root.get("수입자")));     // 이름 + 역할만, ID는 검증된 경우에만
        Payer payerIn        = parsePayerLoose(납세의무자Raw);
        ParsedParty 해외공급자 = parsePartyRobust(S(root.get("해외공급자"))); // Seller & Authenticator
        Payment pay          = parsePayment(S(root.get("결제금액")));          // Incoterm/통화/금액/결제방법

        String[] pkg = splitSimple(S(root.get("총포장갯수"))); // "33, CT"
        String 총포장갯수 = nzBlankIfMissing(idx(pkg, 0));
        String 포장종류   = nzBlankIfMissing(idx(pkg, 1));

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> items =
                (List<Map<String, Object>>) root.getOrDefault("품목별_결과", Collections.emptyList());

        // 2) 상단 공통 세팅 (없으면 공란 유지)
        Element decl = doc.getDocumentElement();

        setText(ensureChildOrdered(doc, decl, "wco:TransactionNatureCode"), 거래구분);

        Element invoice = ensureChildOrdered(doc, decl, "wco:InvoiceAmount");
        setText(invoice, pay.amount);
        setAttrAllowEmpty(invoice, null, "currencyID", pay.currency);

        Element tpq = ensureChildOrdered(doc, decl, "wco:TotalPackageQuantity");
        setText(tpq, 총포장갯수);
        setAttrAllowEmpty(tpq, null, "kcsUnitCode", 포장종류);

        Element cp = ensureChildOrdered(doc, decl, "wco:CustomsProcedure");
        setText(ensureChildOrdered(doc, cp, "kcs:ProcessTypeCode"), 신고구분);
        setText(ensureChildOrdered(doc, cp, "kcs:TypeCode"), 종류);

        Element btm = ensureChildOrdered(doc, decl, "wco:BorderTransportMeans");
        setText(ensureChildOrdered(doc, btm, "wco:Name"), 선기명);

        // 3) GoodsShipment
        Element gs = ensureChildOrdered(doc, decl, "wco:GoodsShipment");
        setText(ensureChildOrdered(doc, gs, "wco:ExportationCountryCode"), 적출국);

        // Seller (무역거래처) – 해외공급자 매핑
        Element seller = ensureChildOrdered(doc, gs, "wco:Seller");
        setText(ensureChildOrdered(doc, seller, "wco:ID"), 해외공급자.code);
        setText(ensureChildOrdered(doc, seller, "wco:Name"), 해외공급자.name);
        Element sAddr = ensureChildOrdered(doc, seller, "wco:Address");
        setText(ensureChildOrdered(doc, sAddr, "wco:CountryCode"), 해외공급자.country);

        // AdditionalDocument/Authenticator – 해외공급자 동일 매핑
        Element addDoc = ensureChildOrdered(doc, gs, "wco:AdditionalDocument");
        Element auth   = ensureChildOrdered(doc, addDoc, "wco:Authenticator");
        setText(ensureChildOrdered(doc, auth, "wco:ID"), 해외공급자.code);
        setText(ensureChildOrdered(doc, auth, "wco:Name"), 해외공급자.name);
        Element aAddr = ensureChildOrdered(doc, auth, "wco:Address");
        setText(ensureChildOrdered(doc, aAddr, "wco:CountryCode"), 해외공급자.country);

        // 무역조건/결제
        Element tt = ensureChildOrdered(doc, gs, "wco:TradeTerms");
        setText(ensureChildOrdered(doc, tt, "wco:ConditionCode"), pay.incoterm);
        setText(ensureChildOrdered(doc, tt, "kcs:SettlementConditionCode"), pay.method);

        // Consignment (B/L 2건, 국내도착항)
        Element cons = ensureChildOrdered(doc, gs, "wco:Consignment");
        Element tcd1 = ensureChildOrdered(doc, cons, "wco:TransportContractDocument");
        setText(ensureChildOrdered(doc, tcd1, "wco:ID"), blNo);
        Element tcd2 = ensureChildOrdered(doc, cons, "wco:TransportContractDocument");
        setText(ensureChildOrdered(doc, tcd2, "wco:ID"), mblNo);
        Element unl = ensureChildOrdered(doc, cons, "wco:UnloadingLocation");
        setText(ensureChildOrdered(doc, unl, "wco:ID"), 국내도착항);

        // 4) Importer
        Element importer = ensureChildOrdered(doc, decl, "wco:Importer");
        setText(ensureChildOrdered(doc, importer, "wco:ID"), importerIn.code);   // 코드가 없으면 공란
        setText(ensureChildOrdered(doc, importer, "wco:Name"), importerIn.name); // 예: "Kumanit Solutions Co., Ltd."
        setText(ensureChildOrdered(doc, importer, "wco:RoleCode"), importerIn.role); // 예: "A"

        // 5) Payer (납세의무자)
        Element payer = ensureChildOrdered(doc, decl, "wco:Payer");
        setText(ensureChildOrdered(doc, payer, "wco:Name"), payerIn.company);
        Element payerAddr = ensureChildOrdered(doc, payer, "wco:Address");
        setText(ensureChildOrdered(doc, payerAddr, "wco:CountrySubDivisionID"), ""); // 입력 없음 → 공란
        setText(ensureChildOrdered(doc, payerAddr, "wco:Line"), payerIn.address);
        setText(ensureChildOrdered(doc, payerAddr, "wco:PostcodeID"), payerIn.postcode);
        setText(ensureChildOrdered(doc, payerAddr, "kcs:BuildingNumber"), "");
        setText(ensureChildOrdered(doc, payerAddr, "kcs:Description"), "");
        Element payerContact = ensureChildOrdered(doc, payer, "wco:Contact");
        setText(ensureChildOrdered(doc, payerContact, "wco:Name"), payerIn.person);
        // 통신 2칸 템플릿 유지: 값 없으면 공란
        Element payerComm1 = ensureChildOrdered(doc, payer, "wco:Communication");
        setText(ensureChildOrdered(doc, payerComm1, "wco:TypeID"), "");
        setText(ensureChildOrdered(doc, payerComm1, "wco:ID"), "");
        Element payerComm2 = ensureChildOrdered(doc, payer, "wco:Communication");
        setText(ensureChildOrdered(doc, payerComm2, "wco:TypeID"), "");
        setText(ensureChildOrdered(doc, payerComm2, "wco:ID"), "");

        // 6) 품목 (템플릿 내 기존 GovernmentAgencyGoodsItem 제거 후, 순서 유지하며 재작성)
        ImportOrigin io = parseImportOrigin(원산지Raw);
        removeDirectChildren(gs, NS_WCO, "GovernmentAgencyGoodsItem");

        for (int i = 0; i < items.size(); i++) {
            Map<String, Object> it = items.get(i);

            String 거래품명  = S(it.get("거래품명"));
            String 세번      = S(it.get("세번번호"));
            String 모델규격  = S(it.get("모델규격"));
            String 단가      = cleanNum(S(it.get("단가")));
            String 품목금액  = cleanNum(S(it.get("금액")));
            String 순중량    = cleanNum(S(it.get("순중량")));
            String 품목포장  = S(it.get("총포장갯수"));
            Quantity q       = parseQty(S(it.get("수량"))); // "4.0000  \nMeter" 등

            Element gag = createChildOrdered(doc, gs, "wco:GovernmentAgencyGoodsItem");
            setText(ensureChildOrdered(doc, gag, "wco:SequenceNumeric"), String.valueOf(i + 1));

            Element cmd = ensureChildOrdered(doc, gag, "wco:Commodity");
            setText(ensureChildOrdered(doc, cmd, "wco:CargoDescription"), 거래품명);

            Element cls = ensureChildOrdered(doc, cmd, "wco:Classification");
            setText(ensureChildOrdered(doc, cls, "wco:ID"), 세번);

            Element cq = ensureChildOrdered(doc, cmd, "wco:CountQuantity");
            setText(cq, q.value);
            setAttrAllowEmpty(cq, NS_KCS, "kcs:UnitCode", q.unit); // 단위 없으면 공란

            Element det = ensureChildOrdered(doc, cmd, "wco:DetailedCommodity");
            setText(ensureChildOrdered(doc, det, "wco:Description"), 모델규격);
            setText(ensureChildOrdered(doc, det, "wco:UnitPriceAmount"), 단가);
            setText(ensureChildOrdered(doc, det, "wco:ValueAmount"), 품목금액);

            Element gm = ensureChildOrdered(doc, gag, "wco:GoodsMeasure");
            Element nnw = ensureChildOrdered(doc, gm, "wco:NetNetWeightMeasure");
            setText(nnw, 순중량);
            setAttrAllowEmpty(nnw, NS_KCS, "kcs:UnitCode", isBlank(순중량) ? "" : "KG");

            if (!isBlank(품목포장)) {
                Element pkgEl = ensureChildOrdered(doc, gag, "wco:Packaging");
                setText(ensureChildOrdered(doc, pkgEl, "wco:QuantityQuantity"), 품목포장);
            }

            Element ori = ensureChildOrdered(doc, gag, "wco:Origin");
            setText(ensureChildOrdered(doc, ori, "wco:CountryCode"), io.country);
            setText(ensureChildOrdered(doc, ori, "wco:RuleCode"), io.rule);
            Element od = ensureChildOrdered(doc, ori, "wco:OriginDescription");
            setText(ensureChildOrdered(doc, od, "kcs:DisplayIndicatorCode"), io.display);
            setText(ensureChildOrdered(doc, od, "kcs:MarksNumbersID"), io.mark);
            setText(ensureChildOrdered(doc, od, "kcs:NonDescriptionReason"), io.nonReason);
        }

        // 7) 직렬화 (byte[])
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
    private String pathOf(Element el, String parentPath){ return parentPath + (parentPath.endsWith("/")?"":"/") + qname(el); }
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
        if (!hasElementChild) el.setTextContent(""); // 리프만 공란
        for (int i = 0; i < nl.getLength(); i++) {
            Node n = nl.item(i);
            if (n.getNodeType() == Node.ELEMENT_NODE) wipeTemplateValues((Element) n);
        }
    }

    // ---------- Setters / Utils ----------
    private void setText(Element el, String value){ el.setTextContent(isBlank(value) ? "" : value); }
    private void setAttrAllowEmpty(Element el, String ns, String qname, String value){
        if (ns==null) el.setAttribute(qname, isBlank(value) ? "" : value);
        else el.setAttributeNS(ns, qname, isBlank(value) ? "" : value);
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
    private static Object coalesce(Map<String,Object> map, String... keys){
        for (String k: keys){ Object v = map.get(k); if (v!=null) return v; }
        return null;
    }
    private static boolean isBlank(String s){
        if (s == null) return true;
        String t = s.trim();
        if (t.isEmpty()) return true;
        String norm = t.replaceAll("[\\s·\\-_/]", "").toLowerCase();
        return "미기재".equals(t) || "미기재".equals(norm) || "migijae".equals(norm) || "-".equals(t);
    }
    private static String nzBlankIfMissing(String s){ return isBlank(s) ? "" : s.trim(); }
    private static String[] splitSimple(String s){ return isBlank(s)? new String[0] : s.split(","); }
    private static String idx(String[] a,int i){ return (a!=null && i<a.length)? a[i].trim() : ""; }
    private static List<String> splitTokens(String s){
        if (isBlank(s)) return new ArrayList<>();
        String[] arr = s.split(",");
        List<String> out = new ArrayList<>();
        for (String a : arr){
            String v = nzBlankIfMissing(a);
            if (!v.isEmpty()) out.add(v);   // '미기재' 토큰 제거
        }
        return out;
    }
    private static String firstToken(String s){ if (isBlank(s)) return ""; int p=s.indexOf(','); return p<0? s.trim(): s.substring(0,p).trim(); }
    private static String cleanNum(String s){ return isBlank(s)? "" : s.replaceAll("[,\\s]", ""); }

    // 결제금액 robust 파싱: [0]=Incoterm, [1]=통화, [2..n-2]=금액, [n-1]=결제방법
    private Payment parsePayment(String raw){
        List<String> t = splitTokens(raw);
        if (t.isEmpty()) return new Payment("","","","");
        String incoterm = t.size()>=1 ? t.get(0) : "";
        String currency = t.size()>=2 ? t.get(1) : "";
        String method   = t.size()>=3 ? t.get(t.size()-1) : "";
        StringBuilder amt = new StringBuilder();
        for (int i=2;i<t.size()-1;i++) amt.append(t.get(i));
        String amount = cleanNum(amt.toString());
        return new Payment(incoterm, currency, amount, method);
    }
    private static class Payment { final String incoterm, currency, amount, method;
        Payment(String i,String c,String a,String m){incoterm=i;currency=c;amount=a;method=m;} }

    // 수입자: 마지막 토큰이 1~2자 알파벳(A/B 등)이면 RoleCode, 그 외는 이름에 포함
    // 코드(ID)는 "영숫자 5+자" 등 명확한 패턴일 때만 인식. 그 외(예: 'Ltd.')는 이름에 포함.
    private Importer parseImporterStrict(String raw){
        List<String> t = splitTokens(raw);
        if (t.isEmpty()) return new Importer("", "", "");
        String role = "";
        if (!t.isEmpty()) {
            String last = t.get(t.size()-1);
            if (last.matches("^[A-Z]{1,2}$")) { role = last; t.remove(t.size()-1); }
        }
        String code = "";
        // 코드로 인정: 영숫자 5+자(숫자 포함), 점(.) 없는 값
        if (!t.isEmpty()) {
            String cand = t.get(t.size()-1);
            if (cand.matches("(?i)^(?=.*\\d)[A-Za-z0-9\\-]{5,}$")) {
                code = cand;
                t.remove(t.size()-1);
            }
        }
        String name = String.join(", ", t).trim();
        return new Importer(name, code, role);
    }
    private static class Importer { final String name, code, role;
        Importer(String n,String c,String r){name=n;code=c;role=r;} }

    // 납세의무자: [우편번호, 주소, 회사명]만 사용, 나머지는 공란
    private Payer parsePayerLoose(String raw){
        List<String> t = splitTokens(raw);
        String postcode = t.size()>=1 ? t.get(0) : "";
        String address  = t.size()>=2 ? t.get(1) : "";
        String company  = t.size()>=3 ? t.get(2) : "";
        return new Payer(postcode, address, company, "", "", "");
    }
    private static class Payer { final String postcode,address,company,phone,email,person;
        Payer(String p,String a,String c,String ph,String em,String pe){postcode=p;address=a;company=c;phone=ph;email=em;person=pe;} }

    // 해외공급자: 코드(영숫자 8~20) + 국가(2자리) + 나머지 이름.
    // "Motec Technology Co., Ltd.KR CNTOSHIN12347" 처럼 붙은 국가코드도 제거.
    private ParsedParty parsePartyRobust(String raw){
        if (isBlank(raw)) return new ParsedParty("","","");
        String s = raw.trim();
        String upper = s.toUpperCase(Locale.ROOT);

        Matcher mCode = Pattern.compile("([A-Z0-9]{8,20})").matcher(upper);
        String code = ""; int codeStart = -1;
        while (mCode.find()) { code = mCode.group(1); codeStart = mCode.start(); }

        String country = "";
        if (codeStart >= 0) {
            Matcher m2 = Pattern.compile("\\b([A-Z]{2})\\b").matcher(upper.substring(0, codeStart));
            while (m2.find()) country = m2.group(1);
        }

        String name = s;
        if (!code.isEmpty()) name = name.replace(code, "");
        // 공백/구두점으로 붙은 국가코드 제거 (예: "Ltd.KR", "Ltd KR", "Ltd, KR")
        if (!country.isEmpty()) {
            name = name.replaceFirst("\\s*[\\.,]?\\s*"+country+"\\s*$", "");
            name = name.replaceFirst("\\s+"+country+"\\b", " ");
        }
        name = name.replace("미기재","").replaceAll("\\s{2,}", " ").trim();
        if (name.endsWith(",")) name = name.substring(0, name.length()-1).trim();

        return new ParsedParty(name, country, code);
    }
    private static class ParsedParty { final String name, country, code;
        ParsedParty(String n,String c,String cd){name=n;country=c;code=cd;} }

    private static class Quantity { final String value, unit; Quantity(String v,String u){value=v;unit=u;} }
    private Quantity parseQty(String raw){
        if (isBlank(raw)) return new Quantity("", "");
        String s = raw.replace("\n"," ").trim();
        Matcher m = Pattern.compile("([0-9]+(?:\\.[0-9]+)?)").matcher(s);
        String val = m.find()? m.group(1) : "";
        String unit = "";
        String tail = s.replaceFirst(Pattern.quote(val), "").trim().toUpperCase(Locale.ROOT);
        if (!isBlank(tail)){
            String u = tail.split("\\s+")[0];
            if      (u.startsWith("METER") || u.equals("M"))  unit="M";
            else if (u.equals("PCS") || u.equals("EA"))       unit=u;
            else if (u.equals("KG") || u.equals("KGM"))       unit="KG";
        }
        return new Quantity(val, unit);
    }

    // 수입 원산지 CSV: "KR, A, Y, B, 01"
    private static class ImportOrigin { final String country, rule, display, mark, nonReason;
        ImportOrigin(String c,String r,String d,String m,String n){country=c;rule=r;display=d;mark=m;nonReason=n;} }
    private ImportOrigin parseImportOrigin(String raw){
        List<String> p = splitTokens(raw);
        String c = p.size()>=1? p.get(0):"";
        String r = p.size()>=2? p.get(1):"";
        String d = p.size()>=3? p.get(2):"";
        String m = p.size()>=4? p.get(3):"";
        String n = p.size()>=5? p.get(4):"";
        return new ImportOrigin(c,r,d,m,n);
    }
}
