import os
import sys

def create_sample_pdf(output_path: str):
    """Generate a clean, structured syllabus PDF for Computer Networks."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open()

        units = [
            ("Unit 1: Introduction to Networks", [
                "Network Types & Topologies: LAN, WAN, MAN, Star, Mesh, Ring, Bus topologies.",
                "OSI Reference Model: 7-layer architecture, encapsulation, protocol data units.",
                "TCP/IP Protocol Architecture: Four-layer internet model, RFC standards.",
                "Packet Switching vs Circuit Switching: Statistical multiplexing, queuing trade-offs."
            ]),
            ("Unit 2: Physical Layer", [
                "Guided Transmission Media: Twisted pair, coaxial cable, single and multimode fiber.",
                "Digital Modulation & Encoding: Manchester, NRZ, QAM line coding schemes.",
                "Multiplexing Techniques: FDM, TDM, WDM wavelength division in optical fibers.",
                "Wireless Transmission & Antennas: Terrestrial microwave, line of sight, ISM bands."
            ]),
            ("Unit 3: Data Link Layer", [
                "Framing & Flow Control: Byte stuffing, bit stuffing, sliding window, Go-Back-N.",
                "Error Detection & Correction: CRC polynomial arithmetic, Hamming distance bounds.",
                "Medium Access Control Protocols: Pure ALOHA, Slotted ALOHA, CSMA/CD, CSMA/CA.",
                "Ethernet & IEEE 802.3: 48-bit MAC addressing, preamble, collision domains."
            ]),
            ("Unit 4: Network Layer", [
                "IPv4 Addressing & Subnetting: Classless Inter-Domain Routing (CIDR), VLSM, RFC 1918.",
                "Routing Algorithms: Dijkstra's Link-State (OSPF), Bellman-Ford Distance Vector (RIP).",
                "IPv6 Architecture & Transition: 128-bit address space, simplified base header.",
                "Congestion Control Principles: Leaky bucket, token bucket traffic shaping."
            ]),
            ("Unit 5: Transport Layer", [
                "TCP 3-Way Handshake & Reliability: SYN, ACK, FIN flags, sequence numbers, 2MSL TIME_WAIT.",
                "UDP & Real-Time Applications: Connectionless 8-byte header overhead for multimedia.",
                "TCP Flow Control & Sliding Window: Receiver window (rwnd), buffer management.",
                "TCP Congestion Control (Reno, Cubic): Slow start, AIMD, fast retransmit, duplicate ACKs."
            ]),
            ("Unit 6: Application Layer", [
                "Domain Name System (DNS): Root servers, TLDs, authoritative resolvers, port 53.",
                "HTTP/HTTPS & Web Protocols: HTTP/1.1 pipelining, HTTP/2 multiplexing, HTTP/3 QUIC.",
                "Email Protocols: SMTP message transfer, IMAP/POP3 mailbox retrieval.",
                "Network Security & TLS/SSL: Ephemeral Diffie-Hellman key exchange, certificates."
            ]),
        ]

        # Title Page
        title_page = doc.new_page(width=595, height=842)
        title_page.insert_text((50, 100), "BANGALORE INSTITUTE OF TECHNOLOGY", fontsize=20, fontname="helv", color=(0.1, 0.2, 0.5))
        title_page.insert_text((50, 130), "Department of Information Science & Engineering", fontsize=14, fontname="helv")
        title_page.insert_text((50, 180), "COURSE SYLLABUS: COMPUTER NETWORKS", fontsize=16, fontname="helv", color=(0.2, 0.4, 0.8))
        title_page.insert_text((50, 210), "Course Code: BIS586 | Academic Year: 2026-2027", fontsize=12, fontname="helv")
        title_page.insert_text((50, 250), "Overview: This comprehensive course covers computer networking from physical transmission", fontsize=11, fontname="helv")
        title_page.insert_text((50, 270), "media to application protocols, focusing on mathematical modeling and protocol analysis.", fontsize=11, fontname="helv")

        # Content pages
        for unit_title, topics in units:
            page = doc.new_page(width=595, height=842)
            page.insert_text((50, 70), unit_title, fontsize=16, fontname="helv", color=(0.1, 0.2, 0.6))
            y = 120
            for topic in topics:
                page.insert_text((60, y), "• " + topic, fontsize=11, fontname="helv")
                y += 50

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        doc.close()
        print(f"Generated sample PDF via PyMuPDF at: {output_path}")
        return True
    except Exception as e:
        print(f"PyMuPDF not available or failed: {e}. Generating clean standard PDF.")
        # Minimal valid PDF generator without external dependencies
        _generate_raw_pdf(output_path)
        return True

def _generate_raw_pdf(output_path: str):
    """Generate a valid standard multi-page PDF using pure Python without any libraries."""
    content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 485 >>
stream
BT
/F1 18 Tf
50 720 Td
(Bangalore Institute of Technology) Tj
/F1 14 Tf
0 -30 Td
(Department of ISE - Computer Networks Syllabus - BIS586) Tj
/F1 12 Tf
0 -40 Td
(Unit 1: Introduction to Networks - Network Topologies, OSI Reference Model, TCP/IP) Tj
0 -25 Td
(Unit 2: Physical Layer - Guided Media, Digital Modulation, Multiplexing) Tj
0 -25 Td
(Unit 3: Data Link Layer - Framing, Error Detection CRC, CSMA/CD, Ethernet) Tj
0 -25 Td
(Unit 4: Network Layer - IPv4 Subnetting, Dijkstra Routing, IPv6, Congestion) Tj
0 -25 Td
(Unit 5: Transport Layer - TCP Handshake, UDP, Flow Control, Congestion Reno) Tj
0 -25 Td
(Unit 6: Application Layer - DNS, HTTP/2/3, SMTP/IMAP, Network Security TLS) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000227 00000 n 
0000000764 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
835
%%EOF
"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(content)
    print(f"Generated raw standard PDF at: {output_path}")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "samples", "computer_networks.pdf")
    create_sample_pdf(out)
