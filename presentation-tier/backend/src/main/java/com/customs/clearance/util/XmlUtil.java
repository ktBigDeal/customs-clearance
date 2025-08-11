// src/main/java/com/customs/clearance/util/XmlUtil.java
package com.customs.clearance.util;

import org.w3c.dom.*;
import javax.xml.namespace.NamespaceContext;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.xpath.*;
import java.util.Iterator;
import java.util.Map;

public class XmlUtil {
    public static Document load(org.springframework.core.io.Resource r) throws Exception {
        var f = DocumentBuilderFactory.newInstance();
        f.setNamespaceAware(true);
        try (var in = r.getInputStream()) {
            return f.newDocumentBuilder().parse(in);
        }
    }
    public static XPath xp(Map<String,String> ns) {
        var xpf = XPathFactory.newInstance();
        var xp = xpf.newXPath();
        xp.setNamespaceContext(new NamespaceContext() {
            public String getNamespaceURI(String p){ return ns.get(p); }
            public String getPrefix(String uri){ return null; }
            public Iterator<String> getPrefixes(String uri){ return null; }
        });
        return xp;
    }
    public static void set(Node n, String v){ if(n!=null && v!=null && !v.isBlank()) n.setTextContent(v.trim()); }
    public static String onlyNum(String s){
        if (s==null) return null;
        var t = s.replace(",", "").replaceAll("[^0-9.]", " ").trim().split("\\s+");
        return t.length>0 && !t[0].isBlank()? t[0] : null;
    }
}
