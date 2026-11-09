"""
MockProvider: Template-based question generation for Computer Networks topics.
Generates realistic educational questions without requiring any API key.
"""
import random
from typing import List, Optional
from app.llm.base import LLMProvider, QuestionData


# Bloom levels and difficulties
BLOOM_LEVELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
DIFFICULTIES = ["easy", "medium", "hard"]

# Topic-specific content templates for Computer Networks
CN_CONTENT = {
    "OSI Model": {
        "facts": [
            "The OSI model has 7 layers",
            "The Physical layer deals with raw bit transmission",
            "The Data Link layer handles framing and error detection",
            "The Network layer is responsible for routing",
            "The Transport layer provides end-to-end communication",
            "The Session layer manages sessions between applications",
            "The Presentation layer handles data formatting",
            "The Application layer provides network services to applications",
            "TCP/IP model maps roughly onto the OSI model",
        ],
        "mcq_stems": [
            ("Which layer of the OSI model is responsible for routing packets between networks?",
             "Network Layer", ["Network Layer", "Data Link Layer", "Transport Layer", "Physical Layer"]),
            ("Which OSI layer ensures reliable end-to-end data delivery?",
             "Transport Layer", ["Transport Layer", "Network Layer", "Session Layer", "Application Layer"]),
            ("Which OSI layer converts data into signals for transmission over physical media?",
             "Physical Layer", ["Physical Layer", "Data Link Layer", "Network Layer", "Session Layer"]),
            ("Which layer adds a header containing MAC addresses?",
             "Data Link Layer", ["Data Link Layer", "Network Layer", "Physical Layer", "Transport Layer"]),
            ("What is the correct order of layers in the OSI model from top to bottom?",
             "Application, Presentation, Session, Transport, Network, Data Link, Physical",
             ["Application, Presentation, Session, Transport, Network, Data Link, Physical",
              "Physical, Data Link, Network, Transport, Session, Presentation, Application",
              "Application, Transport, Network, Data Link, Physical, Session, Presentation",
              "Session, Application, Presentation, Transport, Network, Data Link, Physical"]),
        ],
        "tf_stems": [
            ("The OSI model has exactly 7 layers.", True),
            ("The Transport layer of the OSI model is responsible for routing.", False),
            ("The Presentation layer handles data encryption and compression.", True),
            ("MAC addresses are used at the Network layer.", False),
        ],
    },
    "TCP/IP": {
        "facts": [
            "TCP provides reliable, connection-oriented communication",
            "UDP is connectionless and faster but unreliable",
            "IP is responsible for addressing and routing",
            "TCP uses a 3-way handshake: SYN, SYN-ACK, ACK",
            "TCP has flow control using sliding window protocol",
            "IP addresses are 32-bit (IPv4) or 128-bit (IPv6)",
            "Port numbers identify specific applications",
            "TCP/IP has 4 layers: Application, Transport, Internet, Network Access",
        ],
        "mcq_stems": [
            ("Which protocol provides reliable, ordered delivery of data?",
             "TCP", ["TCP", "UDP", "IP", "ICMP"]),
            ("What is the first step in the TCP 3-way handshake?",
             "SYN", ["SYN", "ACK", "SYN-ACK", "FIN"]),
            ("Which field in the TCP header is used for flow control?",
             "Window Size", ["Window Size", "Sequence Number", "Checksum", "Acknowledgment Number"]),
            ("What is the size of an IPv4 address?",
             "32 bits", ["32 bits", "64 bits", "128 bits", "16 bits"]),
            ("Which protocol is used to test connectivity between hosts?",
             "ICMP", ["ICMP", "TCP", "UDP", "ARP"]),
        ],
        "tf_stems": [
            ("TCP is a connectionless protocol.", False),
            ("UDP provides faster but unreliable data delivery compared to TCP.", True),
            ("IPv6 addresses are 128 bits long.", True),
            ("The TCP 3-way handshake starts with an ACK packet.", False),
        ],
    },
    "IP Addressing": {
        "facts": [
            "IPv4 uses 32-bit addresses written in dotted decimal notation",
            "A subnet mask determines the network and host portions of an IP address",
            "CIDR notation expresses subnet masks as /prefix_length",
            "Class A networks have a first octet range of 1-126",
            "Private IP ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x",
            "Subnetting allows division of a network into smaller segments",
            "VLSM allows different subnet sizes within the same network",
            "NAT translates private IP addresses to public addresses",
        ],
        "mcq_stems": [
            ("What is the default subnet mask for a Class C network?",
             "255.255.255.0", ["255.255.255.0", "255.0.0.0", "255.255.0.0", "255.255.255.255"]),
            ("Which of the following is a private IP address range?",
             "192.168.0.0/16", ["192.168.0.0/16", "200.100.0.0/16", "172.32.0.0/16", "8.8.8.0/24"]),
            ("How many host addresses are available in a /24 subnet?",
             "254", ["254", "256", "255", "253"]),
            ("Which notation is used to represent a subnet mask as /24?",
             "CIDR notation", ["CIDR notation", "Binary notation", "Hexadecimal notation", "Dotted decimal"]),
            ("What is the broadcast address for the network 192.168.1.0/24?",
             "192.168.1.255", ["192.168.1.255", "192.168.1.0", "192.168.1.1", "192.168.1.254"]),
        ],
        "tf_stems": [
            ("IPv4 addresses are 32 bits long.", True),
            ("The address 172.16.0.1 is a public IP address.", False),
            ("CIDR notation /24 is equivalent to the subnet mask 255.255.255.0.", True),
            ("A /25 subnet provides 128 usable host addresses.", False),
        ],
    },
    "Routing Protocols": {
        "facts": [
            "RIP uses hop count as its metric (max 15 hops)",
            "OSPF uses Dijkstra's shortest path first algorithm",
            "BGP is the routing protocol used on the Internet",
            "Distance vector protocols exchange routing tables",
            "Link state protocols exchange topology information",
            "OSPF uses cost based on bandwidth",
            "EIGRP is a Cisco proprietary hybrid routing protocol",
            "Administrative distance determines protocol preference",
        ],
        "mcq_stems": [
            ("Which routing protocol uses hop count as its primary metric?",
             "RIP", ["RIP", "OSPF", "BGP", "EIGRP"]),
            ("What algorithm does OSPF use to calculate shortest paths?",
             "Dijkstra's algorithm", ["Dijkstra's algorithm", "Bellman-Ford algorithm", "Floyd-Warshall algorithm", "Prim's algorithm"]),
            ("Which protocol is used for routing between autonomous systems on the Internet?",
             "BGP", ["BGP", "OSPF", "RIP", "EIGRP"]),
            ("What is the maximum hop count supported by RIP?",
             "15", ["15", "255", "16", "100"]),
            ("Which type of routing protocol exchanges full routing tables with neighbors?",
             "Distance vector", ["Distance vector", "Link state", "Path vector", "Hybrid"]),
        ],
        "tf_stems": [
            ("OSPF is a link-state routing protocol.", True),
            ("RIP supports a maximum of 15 hops before a destination is considered unreachable.", True),
            ("BGP is primarily used for routing within a single organization.", False),
            ("OSPF uses hop count as its routing metric.", False),
        ],
    },
    "Network Security": {
        "facts": [
            "Firewalls filter network traffic based on rules",
            "SSL/TLS encrypts data in transit",
            "AES is a symmetric encryption algorithm",
            "RSA is an asymmetric encryption algorithm",
            "A DMZ separates public and private network segments",
            "IDS detects but doesn't prevent attacks; IPS prevents them",
            "VPNs create encrypted tunnels over public networks",
            "DoS attacks overwhelm a target with traffic",
        ],
        "mcq_stems": [
            ("Which protocol is used to secure web communications?",
             "TLS", ["TLS", "FTP", "HTTP", "SMTP"]),
            ("What is the purpose of a DMZ in network security?",
             "To isolate public-facing servers from the internal network",
             ["To isolate public-facing servers from the internal network",
              "To block all incoming traffic",
              "To increase network speed",
              "To provide wireless access"]),
            ("Which type of attack floods a server with requests to make it unavailable?",
             "Denial of Service (DoS)", ["Denial of Service (DoS)", "Man-in-the-Middle", "SQL Injection", "Phishing"]),
            ("What encryption type uses different keys for encryption and decryption?",
             "Asymmetric encryption", ["Asymmetric encryption", "Symmetric encryption", "Hashing", "Steganography"]),
            ("Which device can both detect and prevent network intrusions?",
             "IPS (Intrusion Prevention System)", ["IPS (Intrusion Prevention System)", "IDS (Intrusion Detection System)", "Firewall", "Router"]),
        ],
        "tf_stems": [
            ("SSL/TLS encrypts data transmitted over a network.", True),
            ("A firewall can prevent all types of cyber attacks.", False),
            ("VPNs use encryption to secure data over public networks.", True),
            ("An IDS actively blocks malicious traffic.", False),
        ],
    },
    "Ethernet and LAN": {
        "facts": [
            "Ethernet uses CSMA/CD for collision detection",
            "A switch operates at the Data Link layer",
            "A hub broadcasts to all ports",
            "MAC addresses are 48 bits (6 bytes) long",
            "VLAN logically separates a LAN into segments",
            "Fast Ethernet operates at 100 Mbps",
            "Gigabit Ethernet operates at 1000 Mbps",
            "STP prevents loops in Ethernet networks",
        ],
        "mcq_stems": [
            ("What access method does Ethernet use to handle collisions?",
             "CSMA/CD", ["CSMA/CD", "CSMA/CA", "Token passing", "TDMA"]),
            ("At which OSI layer does a switch operate?",
             "Data Link Layer", ["Data Link Layer", "Network Layer", "Physical Layer", "Transport Layer"]),
            ("What is the length of a MAC address?",
             "48 bits", ["48 bits", "32 bits", "64 bits", "128 bits"]),
            ("Which technology is used to prevent loops in Ethernet networks?",
             "Spanning Tree Protocol (STP)", ["Spanning Tree Protocol (STP)", "VLAN", "CSMA/CD", "NAT"]),
            ("What is the purpose of a VLAN?",
             "To logically segment a network without physical separation",
             ["To logically segment a network without physical separation",
              "To increase network bandwidth",
              "To connect two different networks",
              "To assign IP addresses automatically"]),
        ],
        "tf_stems": [
            ("A network switch broadcasts packets to all connected devices.", False),
            ("MAC addresses are hardware addresses burned into network interface cards.", True),
            ("CSMA/CD is used in wireless networks.", False),
            ("VLANs require separate physical hardware to segment a network.", False),
        ],
    },
    "DNS": {
        "facts": [
            "DNS resolves domain names to IP addresses",
            "Root DNS servers are at the top of the hierarchy",
            "A DNS query can be recursive or iterative",
            "DNS uses port 53",
            "A records map domain names to IPv4 addresses",
            "AAAA records map domain names to IPv6 addresses",
            "MX records specify mail servers",
            "DNS caching reduces lookup time",
            "TTL determines how long a DNS record is cached",
        ],
        "mcq_stems": [
            ("What port does DNS use by default?",
             "53", ["53", "80", "443", "21"]),
            ("Which DNS record type maps a domain name to an IPv4 address?",
             "A record", ["A record", "AAAA record", "MX record", "CNAME record"]),
            ("What is the role of a recursive DNS resolver?",
             "To query multiple DNS servers on behalf of the client",
             ["To query multiple DNS servers on behalf of the client",
              "To store all DNS records",
              "To block DNS queries",
              "To assign domain names"]),
            ("Which DNS record type is used for mail server lookup?",
             "MX", ["MX", "A", "CNAME", "PTR"]),
            ("What does TTL stand for in DNS?",
             "Time To Live", ["Time To Live", "Total Transfer Latency", "Time To Lookup", "Transfer Time Limit"]),
        ],
        "tf_stems": [
            ("DNS uses port 80 for queries.", False),
            ("A DNS AAAA record maps a hostname to an IPv6 address.", True),
            ("DNS caching helps reduce the load on DNS servers.", True),
            ("Root DNS servers store the records for every website on the Internet.", False),
        ],
    },
    "HTTP and Web": {
        "facts": [
            "HTTP is stateless; HTTPS is HTTP with TLS encryption",
            "HTTP uses port 80; HTTPS uses port 443",
            "REST APIs use HTTP methods: GET, POST, PUT, DELETE",
            "HTTP/2 supports multiplexing multiple requests",
            "Cookies maintain state in HTTP sessions",
            "HTTP status codes: 2xx success, 4xx client error, 5xx server error",
            "Content-Type header specifies the media type",
            "HTTP/3 uses QUIC instead of TCP",
        ],
        "mcq_stems": [
            ("Which HTTP method is used to retrieve data from a server?",
             "GET", ["GET", "POST", "PUT", "DELETE"]),
            ("What port does HTTPS use by default?",
             "443", ["443", "80", "8080", "8443"]),
            ("Which HTTP status code indicates a successful request?",
             "200", ["200", "404", "500", "301"]),
            ("What does HTTP status code 404 indicate?",
             "Resource not found", ["Resource not found", "Server error", "Unauthorized", "Redirect"]),
            ("Which HTTP version introduced multiplexing?",
             "HTTP/2", ["HTTP/2", "HTTP/1.0", "HTTP/1.1", "HTTP/3"]),
        ],
        "tf_stems": [
            ("HTTP is a stateful protocol that remembers previous requests.", False),
            ("HTTPS encrypts data using TLS.", True),
            ("HTTP uses port 443 by default.", False),
            ("A 404 status code means the server encountered an error.", False),
        ],
    },
}

# Generic templates for unknown topics
GENERIC_MCQ_TEMPLATES = [
    ("Which of the following best describes {topic}?",
     "A fundamental networking concept that enables data communication",
     ["A fundamental networking concept that enables data communication",
      "A hardware component used for physical transmission",
      "A protocol for error correction only",
      "A method for user authentication"]),
    ("What is the primary function of {topic} in computer networks?",
     "To facilitate reliable data exchange between network nodes",
     ["To facilitate reliable data exchange between network nodes",
      "To physically connect devices",
      "To assign unique identifiers to users",
      "To provide power to network devices"]),
    ("Which layer of the OSI model is most closely associated with {topic}?",
     "Network Layer",
     ["Network Layer", "Physical Layer", "Application Layer", "Data Link Layer"]),
    ("What problem does {topic} primarily solve in networking?",
     "Ensuring efficient and reliable data transmission",
     ["Ensuring efficient and reliable data transmission",
      "Reducing hardware costs",
      "Managing physical cable installation",
      "Preventing unauthorized physical access"]),
]

GENERIC_TF_TEMPLATES = [
    ("{topic} is an important concept in modern computer networks.", True),
    ("{topic} operates independently of other network protocols.", False),
    ("Understanding {topic} is essential for network troubleshooting.", True),
    ("{topic} was developed specifically for wireless networks.", False),
]

SHORT_ANSWER_TEMPLATES = [
    ("Explain the key components and functions of {topic} in computer networks.",
     "understand", "medium"),
    ("Describe how {topic} contributes to network reliability and performance.",
     "analyze", "hard"),
    ("Compare {topic} with alternative approaches and explain when each is preferred.",
     "evaluate", "hard"),
    ("Explain the relationship between {topic} and the OSI model layers.",
     "understand", "medium"),
    ("What are the advantages and limitations of {topic}?",
     "analyze", "hard"),
    ("How does {topic} handle error detection and correction?",
     "apply", "medium"),
]


class MockProvider(LLMProvider):
    """
    Template-based question generator for educational content.
    Generates realistic Computer Networks questions without any API key.
    """

    def generate_questions(
        self,
        topic_name: str,
        topic_keywords: List[str],
        source_text: str,
        count: int = 5,
        difficulty: str = "mixed",
    ) -> List[QuestionData]:
        """Generate questions for a given topic."""
        questions = []

        # Find the best matching content template
        content = self._find_content(topic_name, topic_keywords)

        # Determine difficulty distribution
        difficulties = self._get_difficulty_distribution(difficulty, count)

        # Generate different question types
        mcq_count = max(1, count * 3 // 5)  # ~60% MCQ
        tf_count = max(1, count // 5)        # ~20% T/F
        sa_count = count - mcq_count - tf_count  # remaining short answer

        questions.extend(self._gen_mcq(topic_name, content, mcq_count, difficulties))
        questions.extend(self._gen_tf(topic_name, content, tf_count, difficulties))
        questions.extend(self._gen_short_answer(topic_name, sa_count, difficulties))

        # Shuffle and trim to requested count
        random.shuffle(questions)
        return questions[:count]

    def _find_content(self, topic_name: str, keywords: List[str]) -> Optional[dict]:
        """Find matching content templates for the topic."""
        topic_lower = topic_name.lower()
        for key, content in CN_CONTENT.items():
            if key.lower() in topic_lower or topic_lower in key.lower():
                return content
        # Try keyword matching
        for kw in keywords:
            for key, content in CN_CONTENT.items():
                if kw.lower() in key.lower():
                    return content
        return None  # Will use generic templates

    def _get_difficulty_distribution(self, difficulty: str, count: int) -> List[str]:
        """Get a list of difficulties for questions."""
        if difficulty == "mixed":
            difficulties = []
            for i in range(count):
                difficulties.append(DIFFICULTIES[i % len(DIFFICULTIES)])
            return difficulties
        return [difficulty] * count

    def _gen_mcq(
        self,
        topic_name: str,
        content: Optional[dict],
        count: int,
        difficulties: List[str],
    ) -> List[QuestionData]:
        """Generate MCQ questions."""
        questions = []
        if content and "mcq_stems" in content:
            stems = list(content["mcq_stems"])
            random.shuffle(stems)
            used = stems[:count]
        else:
            # Use generic templates
            used = []
            for tmpl in GENERIC_MCQ_TEMPLATES[:count]:
                stem = tmpl[0].format(topic=topic_name)
                used.append((stem, tmpl[1], tmpl[2]))

        bloom_choices = ["remember", "understand", "apply", "analyze"]
        for i, (stem, answer, options) in enumerate(used):
            diff = difficulties[i % len(difficulties)] if difficulties else "medium"
            bloom = bloom_choices[i % len(bloom_choices)]
            # Shuffle options
            opts = list(options)
            random.shuffle(opts)
            explanation = self._gen_explanation(topic_name, stem, answer)
            questions.append(QuestionData(
                type="mcq",
                difficulty=diff,
                bloom=bloom,
                stem=stem,
                options=opts,
                answer=answer,
                explanation=explanation,
                source_snippet=f"Refer to the {topic_name} section in the document.",
            ))
        return questions

    def _gen_tf(
        self,
        topic_name: str,
        content: Optional[dict],
        count: int,
        difficulties: List[str],
    ) -> List[QuestionData]:
        """Generate True/False questions."""
        questions = []
        if content and "tf_stems" in content:
            stems = list(content["tf_stems"])
            random.shuffle(stems)
            used = stems[:count]
        else:
            used = []
            for tmpl in GENERIC_TF_TEMPLATES[:count]:
                stmt = tmpl[0].format(topic=topic_name)
                used.append((stmt, tmpl[1]))

        for i, (statement, is_true) in enumerate(used):
            diff = difficulties[i % len(difficulties)] if difficulties else "easy"
            answer = "True" if is_true else "False"
            explanation = (
                f"This statement is {answer.lower()}. {statement} "
                f"{'This is a fundamental principle of ' + topic_name + '.' if is_true else 'This is a common misconception about ' + topic_name + '.'}"
            )
            questions.append(QuestionData(
                type="true_false",
                difficulty=diff,
                bloom="remember" if diff == "easy" else "understand",
                stem=statement,
                options=["True", "False"],
                answer=answer,
                explanation=explanation,
                source_snippet=f"See the {topic_name} section for details.",
            ))
        return questions

    def _gen_short_answer(
        self,
        topic_name: str,
        count: int,
        difficulties: List[str],
    ) -> List[QuestionData]:
        """Generate short answer questions."""
        questions = []
        templates = list(SHORT_ANSWER_TEMPLATES)
        random.shuffle(templates)
        for i, (tmpl, bloom, _) in enumerate(templates[:count]):
            diff = difficulties[i % len(difficulties)] if difficulties else "medium"
            stem = tmpl.format(topic=topic_name)
            answer = (
                f"{topic_name} involves multiple interconnected components. "
                f"Key aspects include its role in the network architecture, "
                f"the protocols it uses, error handling mechanisms, and its "
                f"interaction with adjacent layers or systems. Understanding "
                f"{topic_name} is essential for designing and troubleshooting networks."
            )
            questions.append(QuestionData(
                type="short_answer",
                difficulty=diff,
                bloom=bloom,
                stem=stem,
                options=None,
                answer=answer,
                explanation=f"A comprehensive answer should cover the definition, purpose, mechanisms, and examples of {topic_name}.",
                source_snippet=f"Detailed coverage in the {topic_name} chapter.",
            ))
        return questions

    def _gen_explanation(self, topic_name: str, stem: str, answer: str) -> str:
        """Generate an explanation for an MCQ question."""
        return (
            f"The correct answer is '{answer}'. "
            f"In the context of {topic_name}, this is the most accurate response because "
            f"it reflects the fundamental principles and standards established by networking "
            f"protocols and architectures. Understanding this concept is crucial for "
            f"network design and troubleshooting."
        )
