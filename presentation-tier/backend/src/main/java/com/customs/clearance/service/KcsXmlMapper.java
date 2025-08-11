// src/main/java/com/customs/clearance/service/KcsXmlMapper.java
package com.customs.clearance.service;

import com.customs.clearance.util.XmlUtil;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.w3c.dom.*;

import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathConstants;
import java.io.ByteArrayOutputStream;
import java.util.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

@Service
public class KcsXmlMapper {

    private static final String IMP_PATH = "kcs/KCS_DeclarationOfIMP_929SchemaModule_1.0_standard.xml";
    private static final String EXP_PATH = "kcs/KCS_DeclarationOfEXP_830SchemaModule_1.0_standard.xml";

    // -------------------- PUBLIC API --------------------

    public byte[] buildImportXml(Map<String,Object> details) throws Exception {
        Document doc = XmlUtil.load(new ClassPathResource(IMP_PATH));
        Map<String,String> ns = nsFrom(doc);
        XPath xp = XmlUtil.xp(ns);

        // 상단 합계
        setTotals(doc, xp, details);

        // 운송수단/BL
        upsertTransport(doc, xp, ns, details);
        upsertBLs(doc, xp, ns, details);

        // 다품목
        Element gs = ensureGoodsShipment(doc, ns);
        removeAllChildren(gs, ns.get("wco"), "GovernmentAgencyGoodsItem"); // 초기화
        List<Map<String,Object>> items = getItems(details);
        for (int i = 0; i < items.size(); i++) {
            Map<String,Object> it = items.get(i);
            addItem(doc, xp, ns, gs, it, i + 1); // 1-based
        }

        return toBytes(doc);
    }

    public byte[] buildExportXml(Map<String,Object> details) throws Exception {
        Document doc = XmlUtil.load(new ClassPathResource(EXP_PATH));
        Map<String,String> ns = nsFrom(doc);
        XPath xp = XmlUtil.xp(ns);

        // 상단 합계
        setTotals(doc, xp, details);

        // 운송수단
        upsertTransport(doc, xp, ns, details);

        // 다품목
        Element gs = ensureGoodsShipment(doc, ns);
        removeAllChildren(gs, ns.get("wco"), "GovernmentAgencyGoodsItem");
        List<Map<String,Object>> items = getItems(details);
        for (int i = 0; i < items.size(); i++) {
            Map<String,Object> it = items.get(i);
            addItem(doc, xp, ns, gs, it, i + 1);
        }

        return toBytes(doc);
    }

    // -------------------- CORE MAPPING --------------------

    private void addItem(Document doc, XPath xp, Map<String,String> ns,
                         Element goodsShipment, Map<String,Object> item, int seq) throws Exception {
        Element gag = doc.createElementNS(ns.get("wco"), "wco:GovernmentAgencyGoodsItem");
        goodsShipment.appendChild(gag);

        // 순번
        Element seqEl = doc.createElementNS(ns.get("wco"), "wco:SequenceNumeric");
        seqEl.setTextContent(String.valueOf(seq));
        gag.appendChild(seqEl);

        // Commodity
        Element commodity = doc.createElementNS(ns.get("wco"), "wco:Commodity");
        gag.appendChild(commodity);

        String itemName = getS(item, "거래품명","품명","item_name");
        String modelSpec = getS(item, "모델및규격","모델 및 규격","model_spec");
        setTextChild(doc, commodity, ns.get("wco"), "CargoDescription",
                     firstNonNull(itemName, modelSpec));

        // HS
        Element classification = doc.createElementNS(ns.get("wco"), "wco:Classification");
        commodity.appendChild(classification);
        setTextChild(doc, classification, ns.get("wco"), "ID",
                     XmlUtil.onlyNum(getS(item,"세번번호","세번부호","hs_code")));

        // CountQuantity @kcs:UnitCode="EA"
        Element countQ = doc.createElementNS(ns.get("wco"), "wco:CountQuantity");
        countQ.setAttributeNS(ns.get("kcs"), "kcs:UnitCode", "EA");
        countQ.setTextContent(onlyNumOrNull(getS(item,"수량","quantity")));
        commodity.appendChild(countQ);

        // DetailedCommodity (모델/단가/금액)
        Element detail = doc.createElementNS(ns.get("wco"), "wco:DetailedCommodity");
        commodity.appendChild(detail);
        setTextChild(doc, detail, ns.get("wco"), "Description", modelSpec);
        setTextChild(doc, detail, ns.get("kcs"), "UnitPriceAmount", onlyNumOrNull(getS(item,"단가","unit_price")));
        setTextChild(doc, detail, ns.get("kcs"), "ValueAmount",     onlyNumOrNull(getS(item,"금액","amount")));

        // GoodsMeasure (순중량)
        Element gm = doc.createElementNS(ns.get("wco"), "wco:GoodsMeasure");
        gag.appendChild(gm);
        Element nnw = doc.createElementNS(ns.get("wco"), "wco:NetNetWeightMeasure");
        nnw.setAttributeNS(ns.get("kcs"), "kcs:UnitCode", "KG");
        nnw.setTextContent(onlyNumOrNull(getS(item,"순중량","net_weight")));
        gm.appendChild(nnw);

        // Packaging (품목별 포장수량이 있으면)
        String pkg = getS(item, "포장개수","포장 개수","packages");
        if (pkg != null && !pkg.isBlank()) {
            Element packaging = doc.createElementNS(ns.get("wco"), "wco:Packaging");
            gag.appendChild(packaging);
            setTextChild(doc, packaging, ns.get("wco"), "QuantityQuantity", onlyNumOrNull(pkg));
            setTextChild(doc, packaging, ns.get("wco"), "TypeCode", "CT");
        }
    }

    private void setTotals(Document doc, XPath xp, Map<String,Object> details) throws Exception {
        XmlUtil.set((Node) xp.evaluate("wco:Declaration/wco:TotalGrossMassMeasure", doc, XPathConstants.NODE),
                XmlUtil.onlyNum(getS(details,"총중량","gross_weight")));
        XmlUtil.set((Node) xp.evaluate("wco:Declaration/wco:TotalPackageQuantity", doc, XPathConstants.NODE),
                XmlUtil.onlyNum(getS(details,"총포장개수","total_packages")));
        XmlUtil.set((Node) xp.evaluate("wco:Declaration/wco:InvoiceAmount", doc, XPathConstants.NODE),
                XmlUtil.onlyNum(getS(details,"결제금액","invoice_amount","total_amount")));
    }

    private void upsertTransport(Document doc, XPath xp, Map<String,String> ns, Map<String,Object> details) throws Exception {
        Node border = (Node) xp.evaluate("wco:Declaration/wco:BorderTransportMeans", doc, XPathConstants.NODE);
        if (border == null) {
            border = doc.createElementNS(ns.get("wco"), "wco:BorderTransportMeans");
            doc.getDocumentElement().appendChild(border);
        }
        XmlUtil.set((Node) xp.evaluate("wco:Name", border, XPathConstants.NODE), getS(details,"선기명","vessel_name"));
        XmlUtil.set((Node) xp.evaluate("wco:RegistrationNationalityID", border, XPathConstants.NODE), getS(details,"선박국적","vessel_nationality"));
    }

    private void upsertBLs(Document doc, XPath xp, Map<String,String> ns, Map<String,Object> details) throws Exception {
        Element gs = ensureGoodsShipment(doc, ns);
        Node cons = (Node) xp.evaluate("wco:Consignment", gs, XPathConstants.NODE);
        if (cons == null) {
            cons = doc.createElementNS(ns.get("wco"), "wco:Consignment");
            gs.appendChild(cons);
        }
        upsertTcd(doc, xp, cons, ns, getS(details,"BL_AWB번호","BL_AWB_번호","bl_number","HBL"), "714"); // H-B/L
        upsertTcd(doc, xp, cons, ns, getS(details,"Master_BL_번호","mbl_number","MBL"), "704");        // M-B/L
    }

    // -------------------- HELPERS --------------------

    private static Map<String,String> nsFrom(Document doc){
        return Map.of(
            "wco", doc.getDocumentElement().getNamespaceURI(),
            "kcs", Optional.ofNullable(doc.lookupNamespaceURI("kcs"))
                           .orElse(doc.getDocumentElement().getNamespaceURI())
        );
    }

    private static Element ensureGoodsShipment(Document doc, Map<String,String> ns){
        NodeList list = doc.getElementsByTagNameNS(ns.get("wco"), "GoodsShipment");
        if (list.getLength() > 0) return (Element) list.item(0);
        Element gs = doc.createElementNS(ns.get("wco"), "wco:GoodsShipment");
        doc.getDocumentElement().appendChild(gs);
        return gs;
    }

    private static void upsertTcd(Document doc, XPath xp, Node cons, Map<String,String> ns, String idVal, String typeCode) throws Exception {
        if (idVal == null || idVal.isBlank()) return;
        NodeList list = (NodeList) xp.evaluate("wco:TransportContractDocument", cons, XPathConstants.NODESET);
        for (int i=0;i<list.getLength();i++){
            Node tcd = list.item(i);
            Node tc = (Node) xp.evaluate("wco:TypeCode", tcd, XPathConstants.NODE);
            if (tc!=null && typeCode.equals(tc.getTextContent())) {
                setTextChild(doc, (Element) tcd, ns.get("wco"), "ID", idVal);
                return;
            }
        }
        Element tcd = doc.createElementNS(ns.get("wco"), "wco:TransportContractDocument");
        setTextChild(doc, tcd, ns.get("wco"), "ID", idVal);
        setTextChild(doc, tcd, ns.get("wco"), "TypeCode", typeCode);
        cons.appendChild(tcd);
    }

    private static void setTextChild(Document d, Node parent, String uri, String local, String value){
        if (value == null || value.isBlank()) return;
        Element el = d.createElementNS(uri, "wco:" + local);
        el.setTextContent(value);
        parent.appendChild(el);
    }

    private static void removeAllChildren(Element parent, String uri, String local){
        NodeList nodes = parent.getElementsByTagNameNS(uri, local);
        // NodeList는 live라서 역순 제거
        for (int i = nodes.getLength() - 1; i >= 0; i--) {
            Node n = nodes.item(i);
            if (n.getParentNode() == parent) parent.removeChild(n);
        }
    }

    private static String firstNonNull(String a, String b){ return (a!=null && !a.isBlank())? a : b; }
    private static String getS(Map<String,Object> m, String... keys){
        for (String k : keys){
            Object v = m.get(k);
            if (v != null) return String.valueOf(v);
        }
        return null;
    }
    private static List<Map<String,Object>> getItems(Map<String,Object> details){
        Object v = details.get("품목별_결과");
        if (v instanceof List<?> l && !l.isEmpty() && l.get(0) instanceof Map<?,?>) return (List<Map<String,Object>>) v;
        v = details.get("items");
        if (v instanceof List<?> l2 && !l2.isEmpty() && l2.get(0) instanceof Map<?,?>) return (List<Map<String,Object>>) v;
        return Collections.emptyList();
    }
    private static String onlyNumOrNull(String s){ return s==null? null : XmlUtil.onlyNum(s); }

    private static byte[] toBytes(Document doc) throws Exception {
        Transformer tf = TransformerFactory.newInstance().newTransformer();
        tf.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
        tf.setOutputProperty(OutputKeys.INDENT, "yes");
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        tf.transform(new DOMSource(doc), new StreamResult(out));
        return out.toByteArray();
    }
}
