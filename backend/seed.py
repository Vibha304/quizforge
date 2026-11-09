import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.users import User
from app.models.documents import Document
from app.models.topics import Topic
from app.models.questions import Question
from app.models.quiz import QuizSession, Attempt
from app.models.mastery import Mastery
from app.models.gamification import UserStats, Badge, UserBadge
from app.core.security import get_password_hash
from app.services.gamification.engine import BADGE_DEFINITIONS, _ensure_badges

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

COMPUTER_NETWORKS_UNITS = [
    {
        "unit": "Unit 1: Introduction to Networks",
        "summary": "Foundational networking principles, layered architectural models, topology designs, and switching paradigms.",
        "topics": [
            {
                "name": "Network Types & Topologies",
                "keywords": ["LAN", "WAN", "MAN", "Star", "Mesh", "Ring", "Bus"],
                "summary": "Local, Metropolitan, and Wide Area Networks classifications and physical interconnection geometries.",
                "difficulty_prior": 0.30,
                "initial_mastery": 0.92,
                "attempts": 6,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "Which network topology connects every node to a central hub or switch?",
                        "options": ["Star Topology", "Bus Topology", "Ring Topology", "Mesh Topology"],
                        "answer": "Star Topology",
                        "explanation": "In a star topology, each network host is connected to a central hub or switch with a point-to-point connection.",
                        "source_snippet": "Unit 1, Section 1.1: Physical Topologies and Hub Interconnects.",
                    },
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "In a full mesh topology with n devices, how many physical communication links are required?",
                        "options": ["n(n - 1) / 2", "n(n + 1) / 2", "n - 1", "2n"],
                        "answer": "n(n - 1) / 2",
                        "explanation": "Every node connects directly to every other node without repetition, requiring n(n-1)/2 duplex links.",
                        "source_snippet": "Unit 1, Section 1.2: Mesh topology redundancy formulas.",
                    },
                    {
                        "type": "true_false",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "A Wide Area Network (WAN) typically spans cities, countries, or global distances.",
                        "options": ["True", "False"],
                        "answer": "True",
                        "explanation": "WANs interconnect geographical areas beyond local campuses or municipalities.",
                        "source_snippet": "Unit 1, Section 1.1: Network classifications by geographic scope.",
                    },
                    {
                        "type": "short_answer",
                        "difficulty": "hard",
                        "bloom": "analyze",
                        "stem": "What is the primary single point of failure disadvantage of a star topology compared to a mesh topology?",
                        "options": None,
                        "answer": "central switch failure",
                        "explanation": "If the central hub or switch fails, all attached stations lose communication entirely.",
                        "source_snippet": "Unit 1, Section 1.3: Fault tolerance comparison across network topologies.",
                    },
                ],
            },
            {
                "name": "OSI Reference Model",
                "keywords": ["OSI", "7 Layers", "Encapsulation", "PDU", "ISO"],
                "summary": "The 7-layer ISO/IEC standard architectural model for open computer system communication.",
                "difficulty_prior": 0.35,
                "initial_mastery": 0.94,
                "attempts": 8,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "Which layer of the OSI reference model is responsible for end-to-end process-to-process communication?",
                        "options": ["Transport Layer", "Network Layer", "Data Link Layer", "Session Layer"],
                        "answer": "Transport Layer",
                        "explanation": "The Transport Layer (Layer 4) ensures end-to-end data transfer, flow control, error recovery, and multiplexing between processes.",
                        "source_snippet": "Unit 1, Section 2.4: Layer 4 Transport specifications.",
                    },
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "At which layer of the OSI model does data encryption and compression primarily take place?",
                        "options": ["Presentation Layer", "Application Layer", "Session Layer", "Transport Layer"],
                        "answer": "Presentation Layer",
                        "explanation": "The Presentation Layer (Layer 6) handles syntax translation, compression, and cryptographic transformation.",
                        "source_snippet": "Unit 1, Section 2.6: Presentation Layer data representation standards.",
                    },
                    {
                        "type": "true_false",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "Routers primarily operate at the Data Link Layer (Layer 2) of the OSI model.",
                        "options": ["True", "False"],
                        "answer": "False",
                        "explanation": "Standard routers operate at the Network Layer (Layer 3) to route packets based on logical IP addresses.",
                        "source_snippet": "Unit 1, Section 2.3: Network Layer hardware and forwarding devices.",
                    },
                ],
            },
            {
                "name": "TCP/IP Protocol Architecture",
                "keywords": ["TCP/IP", "Four Layers", "RFC", "Internet Model"],
                "summary": "The practical four-layer Internet reference model powering modern interconnected networks.",
                "difficulty_prior": 0.35,
                "initial_mastery": 0.85,
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "How many layers are formally defined in the standard TCP/IP Internet model?",
                        "options": ["4 Layers", "5 Layers", "7 Layers", "3 Layers"],
                        "answer": "4 Layers",
                        "explanation": "The original TCP/IP model has 4 layers: Link, Internet, Transport, and Application.",
                        "source_snippet": "Unit 1, Section 3.1: TCP/IP RFC 1122 Architecture.",
                    },
                    {
                        "type": "mcq",
                        "difficulty": "hard",
                        "bloom": "apply",
                        "stem": "Which protocol in the TCP/IP stack maps a known IP address to a physical MAC hardware address on a local segment?",
                        "options": ["ARP (Address Resolution Protocol)", "RARP", "ICMP", "IGMP"],
                        "answer": "ARP (Address Resolution Protocol)",
                        "explanation": "ARP broadcasts on the local link to determine the Layer 2 MAC address corresponding to a given target IPv4 address.",
                        "source_snippet": "Unit 1, Section 3.4: Address Resolution Protocol mechanisms.",
                    },
                ],
            },
            {
                "name": "Packet Switching vs Circuit Switching",
                "keywords": ["Store-and-Forward", "Virtual Circuit", "Datagram", "TDM"],
                "summary": "Comparison between dedicated transmission path reservation and statistical multiplexing.",
                "difficulty_prior": 0.40,
                "initial_mastery": 0.78,
                "attempts": 4,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "What is a primary advantage of packet switching over circuit switching for bursty computer data?",
                        "options": [
                            "Higher link utilization through statistical multiplexing",
                            "Guaranteed fixed latency for every transmission",
                            "Zero queuing delay at intermediate buffers",
                            "Constant allocated bandwidth per user",
                        ],
                        "answer": "Higher link utilization through statistical multiplexing",
                        "explanation": "Packet switching allows idle channel bandwidth to be shared on demand rather than remaining blocked.",
                        "source_snippet": "Unit 1, Section 4.2: Statistical multiplexing and queuing trade-offs.",
                    },
                ],
            },
        ],
    },
    {
        "unit": "Unit 2: Physical Layer",
        "summary": "Electromagnetic transmission media, modulation schemes, multiplexing, and physical bit transfer.",
        "topics": [
            {
                "name": "Guided Transmission Media",
                "keywords": ["Twisted Pair", "Coaxial", "Fiber Optic", "Attenuation", "Bandwidth"],
                "summary": "Physical conductors including unshielded twisted pair, coaxial cables, and single/multimode optical fiber.",
                "difficulty_prior": 0.30,
                "initial_mastery": 0.91,
                "attempts": 7,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "Which transmission medium provides the highest data rate and immunity to electromagnetic interference (EMI)?",
                        "options": ["Optical Fiber Cable", "Unshielded Twisted Pair (UTP)", "Coaxial Cable", "Shielded Twisted Pair (STP)"],
                        "answer": "Optical Fiber Cable",
                        "explanation": "Optical fibers transmit light pulses through glass or plastic cores, completely immune to electromagnetic fields.",
                        "source_snippet": "Unit 2, Section 1.3: Optical fiber propagation and refraction characteristics.",
                    },
                    {
                        "type": "true_false",
                        "difficulty": "easy",
                        "bloom": "understand",
                        "stem": "Twisting the copper wire pairs in UTP cables reduces electromagnetic crosstalk between adjacent pairs.",
                        "options": ["True", "False"],
                        "answer": "True",
                        "explanation": "Equal and opposite induced currents cancel out external interference and adjacent pair crosstalk.",
                        "source_snippet": "Unit 2, Section 1.1: Balanced signal cancellation in twisted pair.",
                    },
                ],
            },
            {
                "name": "Digital Modulation & Encoding",
                "keywords": ["Manchester", "NRZ", "QAM", "BPSK", "Baud Rate"],
                "summary": "Line coding formats, carrier modulation methods, Nyquist criteria, and Shannon channel capacity limits.",
                "difficulty_prior": 0.45,
                "initial_mastery": 0.70,
                "attempts": 4,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "apply",
                        "stem": "In Manchester encoding, how is a binary digit signaled on the physical medium?",
                        "options": [
                            "By a voltage transition in the middle of each bit interval",
                            "By remaining high throughout the entire bit duration",
                            "By transitioning only on zero bits",
                            "By three distinct voltage levels",
                        ],
                        "answer": "By a voltage transition in the middle of each bit interval",
                        "explanation": "Manchester ensures clock synchronization by forcing a transition at the center of every bit period.",
                        "source_snippet": "Unit 2, Section 3.2: Self-clocking bi-phase encoding standards.",
                    },
                ],
            },
            {
                "name": "Multiplexing Techniques",
                "keywords": ["FDM", "TDM", "WDM", "CDMA", "Orthogonal"],
                "summary": "Sharing common transmission links across frequency, time, wavelength, and code domains.",
                "difficulty_prior": 0.38,
                "initial_mastery": 0.82,
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "Which multiplexing scheme is specifically used in optical fiber communications to combine multiple wavelengths onto a single strand?",
                        "options": [
                            "WDM (Wavelength Division Multiplexing)",
                            "FDM (Frequency Division Multiplexing)",
                            "TDM (Time Division Multiplexing)",
                            "Spatial Division Multiplexing",
                        ],
                        "answer": "WDM (Wavelength Division Multiplexing)",
                        "explanation": "WDM modulates different data streams onto distinct optical carrier wavelengths (colors) inside the fiber.",
                        "source_snippet": "Unit 2, Section 4.3: Dense Wavelength Division Multiplexing (DWDM).",
                    },
                ],
            },
            {
                "name": "Wireless Transmission & Antennas",
                "keywords": ["Radio Waves", "Microwave", "Infrared", "Line of Sight", "Spectrum"],
                "summary": "Unguided electromagnetic wave propagation, terrestrial microwave, satellite communications, and ISM bands.",
                "difficulty_prior": 0.35,
                "initial_mastery": 0.88,
                "attempts": 4,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "Which frequency band is unguided, requires line-of-sight propagation, and is commonly used for satellite links?",
                        "options": ["Microwave", "Infrared", "Very Low Frequency (VLF)", "Audio Frequency"],
                        "answer": "Microwave",
                        "explanation": "Microwaves (1 GHz to 300 GHz) travel in straight lines, making directional dish alignment critical.",
                        "source_snippet": "Unit 2, Section 2.2: Terrestrial and satellite microwave transmission.",
                    },
                ],
            },
        ],
    },
    {
        "unit": "Unit 3: Data Link Layer",
        "summary": "Framing methods, bit error detection and correction, flow control, and medium access control protocols.",
        "topics": [
            {
                "name": "Framing & Flow Control",
                "keywords": ["Byte Stuffing", "Bit Stuffing", "Stop-and-Wait", "Sliding Window", "Go-Back-N"],
                "summary": "Delineating bit streams into discrete frames and pacing sender output to match receiver buffer capacities.",
                "difficulty_prior": 0.40,
                "initial_mastery": 0.65,
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "apply",
                        "stem": "In HDLC bit-oriented framing, what sequence is inserted when five consecutive '1' bits appear in user data?",
                        "options": [
                            "A '0' bit is stuffed immediately after the five '1' bits",
                            "A '1' bit is stuffed to preserve balance",
                            "An escape character (ESC) is prepended",
                            "The frame is aborted immediately",
                        ],
                        "answer": "A '0' bit is stuffed immediately after the five '1' bits",
                        "explanation": "Bit stuffing prevents the flag delimiter (01111110) from accidentally appearing inside arbitrary user payload.",
                        "source_snippet": "Unit 3, Section 1.2: Bit stuffing algorithms in HDLC.",
                    },
                ],
            },
            {
                "name": "Error Detection & Correction",
                "keywords": ["CRC", "Cyclic Redundancy Check", "Parity", "Hamming Code", "Checksum"],
                "summary": "Mathematical coding techniques including polynomial division CRC and minimum Hamming distance codes.",
                "difficulty_prior": 0.50,
                "initial_mastery": 0.42,  # WEAK TOPIC!
                "attempts": 6,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "hard",
                        "bloom": "analyze",
                        "stem": "To detect d single-bit transmission errors in any codeword, what is the minimum Hamming distance required between valid codewords?",
                        "options": ["d + 1", "2d + 1", "2d", "d"],
                        "answer": "d + 1",
                        "explanation": "A code with minimum distance d+1 ensures that any d or fewer bit errors will produce an invalid non-codeword.",
                        "source_snippet": "Unit 3, Section 2.3: Hamming distance error detection bounds.",
                    },
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "apply",
                        "stem": "In a Cyclic Redundancy Check (CRC) calculation using modulo-2 arithmetic, what mathematical operation is used in place of standard arithmetic subtraction?",
                        "options": ["XOR operation", "AND operation", "OR operation", "Two's complement"],
                        "answer": "XOR operation",
                        "explanation": "Modulo-2 addition and subtraction are identical and correspond to the bitwise Exclusive-OR (XOR) logic.",
                        "source_snippet": "Unit 3, Section 2.1: Polynomial generator division mechanics.",
                    },
                    {
                        "type": "true_false",
                        "difficulty": "easy",
                        "bloom": "understand",
                        "stem": "A simple single-bit parity check can detect all double-bit errors in a received character.",
                        "options": ["True", "False"],
                        "answer": "False",
                        "explanation": "Double-bit errors cancel each other out, leaving the overall parity count identical to the original.",
                        "source_snippet": "Unit 3, Section 2.2: Limitations of simple parity checks.",
                    },
                ],
            },
            {
                "name": "Medium Access Control Protocols",
                "keywords": ["ALOHA", "CSMA/CD", "CSMA/CA", "Exponential Backoff", "Collision Domain"],
                "summary": "Random access and collision arbitration algorithms for shared broadcast physical media.",
                "difficulty_prior": 0.42,
                "initial_mastery": 0.72,
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "What is the maximum theoretical efficiency (throughput) of Pure ALOHA under heavy poisson traffic?",
                        "options": ["18.4% (1 / 2e)", "36.8% (1 / e)", "50.0%", "100%"],
                        "answer": "18.4% (1 / 2e)",
                        "explanation": "Pure ALOHA suffers from a vulnerable period of 2 frames, yielding a peak channel throughput of 1/(2e) ≈ 18.4%.",
                        "source_snippet": "Unit 3, Section 3.1: ALOHA channel throughput analysis.",
                    },
                ],
            },
            {
                "name": "Ethernet & IEEE 802.3",
                "keywords": ["MAC Address", "Preamble", "Gigabit Ethernet", "Switching", "VLAN"],
                "summary": "Ethernet frame format, 48-bit OUI addressing, store-and-forward switching, and collision domain segmentation.",
                "difficulty_prior": 0.32,
                "initial_mastery": 0.90,
                "attempts": 6,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "What is the size of a standard IEEE 802.3 Ethernet physical (MAC) address?",
                        "options": ["48 bits (6 bytes)", "32 bits (4 bytes)", "64 bits (8 bytes)", "128 bits (16 bytes)"],
                        "answer": "48 bits (6 bytes)",
                        "explanation": "MAC addresses are 48 bits long, represented as 12 hexadecimal digits separated by colons or hyphens.",
                        "source_snippet": "Unit 3, Section 4.1: IEEE 802.3 MAC frame structure.",
                    },
                ],
            },
        ],
    },
    {
        "unit": "Unit 4: Network Layer",
        "summary": "Logical addressing, subnet planning, dynamic routing algorithms, and internetworking protocols.",
        "topics": [
            {
                "name": "IPv4 Addressing & Subnetting",
                "keywords": ["CIDR", "Subnet Mask", "VLSM", "Broadcast Address", "Private IP"],
                "summary": "Classful vs Classless Inter-Domain Routing, network/host address bit partitioning, and prefix aggregation.",
                "difficulty_prior": 0.48,
                "initial_mastery": 0.38,  # WEAK TOPIC!
                "attempts": 7,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "hard",
                        "bloom": "apply",
                        "stem": "For the network address 192.168.10.0/27, what is the total number of usable assignable host IP addresses?",
                        "options": ["30 hosts", "32 hosts", "28 hosts", "14 hosts"],
                        "answer": "30 hosts",
                        "explanation": "A /27 mask reserves 5 host bits: 2^5 = 32 addresses minus network ID (all 0s) and directed broadcast (all 1s) = 30.",
                        "source_snippet": "Unit 4, Section 1.3: VLSM address pool calculations.",
                    },
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "Which of the following IP address blocks is designated as a private RFC 1918 non-routable range?",
                        "options": ["172.16.0.0/12", "192.169.0.0/16", "11.0.0.0/8", "169.254.0.0/16"],
                        "answer": "172.16.0.0/12",
                        "explanation": "RFC 1918 reserves 10.0.0.0/8, 172.16.0.0/12 (172.16.0.0–172.31.255.255), and 192.168.0.0/16.",
                        "source_snippet": "Unit 4, Section 1.1: Private IPv4 address allocations.",
                    },
                ],
            },
            {
                "name": "Routing Algorithms",
                "keywords": ["Dijkstra", "OSPF", "Bellman-Ford", "Distance Vector", "BGP", "Split Horizon"],
                "summary": "Shortest-path link-state computation and distributed distance-vector graph routing algorithms.",
                "difficulty_prior": 0.52,
                "initial_mastery": 0.55,  # WEAK TOPIC!
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "hard",
                        "bloom": "analyze",
                        "stem": "What problem occurs in Distance Vector routing when link failures cause routing updates to loop infinitely?",
                        "options": [
                            "Count-to-Infinity Problem",
                            "Silencing Storm Problem",
                            "Split-Brain Cluster Fault",
                            "Routing Table Exhaustion",
                        ],
                        "answer": "Count-to-Infinity Problem",
                        "explanation": "Distance vector routers can propagate out-of-date distance metrics in loops, solved via Split Horizon and Poison Reverse.",
                        "source_snippet": "Unit 4, Section 2.2: Bellman-Ford convergence and count-to-infinity.",
                    },
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "Which shortest-path algorithm is utilized by the Link-State routing protocol OSPF?",
                        "options": ["Dijkstra's Algorithm", "Bellman-Ford Algorithm", "Floyd-Warshall Algorithm", "Kruskal's Algorithm"],
                        "answer": "Dijkstra's Algorithm",
                        "explanation": "OSPF builds a synchronized topology database and applies Dijkstra's shortest-path first algorithm to construct the routing tree.",
                        "source_snippet": "Unit 4, Section 2.1: Link-state packet flooding and Dijkstra SPF.",
                    },
                ],
            },
            {
                "name": "IPv6 Architecture & Transition",
                "keywords": ["128-bit", "Dual Stack", "Anycast", "Header", "SLAAC"],
                "summary": "Next-generation internet protocol with 128-bit addressing, simplified fixed headers, and transition mechanisms.",
                "difficulty_prior": 0.40,
                "initial_mastery": 0.84,
                "attempts": 4,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "What is the fixed base header size of an IPv6 packet without extension headers?",
                        "options": ["40 bytes", "20 bytes", "32 bytes", "64 bytes"],
                        "answer": "40 bytes",
                        "explanation": "IPv6 utilizes a streamlined fixed-length base header of 40 bytes to accelerate router processing.",
                        "source_snippet": "Unit 4, Section 3.1: IPv6 base header format and alignment.",
                    },
                ],
            },
            {
                "name": "Congestion Control Principles",
                "keywords": ["Leaky Bucket", "Token Bucket", "Choke Packet", "Buffer Overflow", "ECN"],
                "summary": "Open-loop traffic shaping (leaky and token buckets) and closed-loop feedback congestion mitigation.",
                "difficulty_prior": 0.45,
                "initial_mastery": 0.62,
                "attempts": 3,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "apply",
                        "stem": "Unlike the Leaky Bucket algorithm, what capability does the Token Bucket traffic shaping algorithm provide?",
                        "options": [
                            "It allows bursty data transmissions up to token capacity",
                            "It completely prevents all buffer drops",
                            "It requires zero buffer space",
                            "It only transmits at a constant unvarying speed",
                        ],
                        "answer": "It allows bursty data transmissions up to token capacity",
                        "explanation": "Token bucket permits bursts when accumulated tokens exist while maintaining long-term average output rates.",
                        "source_snippet": "Unit 4, Section 4.2: Traffic shaping comparison: Token vs Leaky Bucket.",
                    },
                ],
            },
        ],
    },
    {
        "unit": "Unit 5: Transport Layer",
        "summary": "Reliable connection-oriented TCP, lightweight UDP, sliding windows, and AIMD congestion control.",
        "topics": [
            {
                "name": "TCP 3-Way Handshake & Reliability",
                "keywords": ["SYN", "ACK", "FIN", "Sequence Number", "ISN", "TIME_WAIT"],
                "summary": "Connection establishment and termination state machines, retransmission timers, and segment sequencing.",
                "difficulty_prior": 0.42,
                "initial_mastery": 0.74,
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "During a standard TCP connection teardown, why does the initiating client enter the TIME_WAIT state?",
                        "options": [
                            "To ensure the final ACK was received by the remote server and allow old duplicates to expire",
                            "To wait for outstanding data payload still in transit",
                            "To renegotiate the Maximum Segment Size (MSS)",
                            "To reset the local sequence counter back to zero",
                        ],
                        "answer": "To ensure the final ACK was received by the remote server and allow old duplicates to expire",
                        "explanation": "TIME_WAIT lasts 2 MSL (Maximum Segment Lifetime) to retransmit ACK if lost and drain lingering packets from the network.",
                        "source_snippet": "Unit 5, Section 1.3: TCP connection termination and 2MSL TIME_WAIT.",
                    },
                ],
            },
            {
                "name": "UDP & Real-Time Applications",
                "keywords": ["Connectionless", "Header 8 Bytes", "VoIP", "DNS", "Streaming", "No Retransmission"],
                "summary": "Minimalist datagram service with 8-byte header overhead for delay-sensitive audio, video, and gaming traffic.",
                "difficulty_prior": 0.28,
                "initial_mastery": 0.95,
                "attempts": 6,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "What is the total header size of a User Datagram Protocol (UDP) segment?",
                        "options": ["8 bytes", "20 bytes", "16 bytes", "12 bytes"],
                        "answer": "8 bytes",
                        "explanation": "UDP headers contain only 4 fields (Source Port, Destination Port, Length, Checksum) of 2 bytes each, total 8 bytes.",
                        "source_snippet": "Unit 5, Section 2.1: UDP segment layout.",
                    },
                ],
            },
            {
                "name": "TCP Flow Control & Sliding Window",
                "keywords": ["rwnd", "Receive Buffer", "Zero Window", "Silly Window Syndrome", "Nagle Algorithm"],
                "summary": "Receiver-driven buffer advertisement to prevent fast senders from swamping slower receivers.",
                "difficulty_prior": 0.45,
                "initial_mastery": 0.68,
                "attempts": 4,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "What parameter does a TCP receiver advertise in each segment header to constrain sender output?",
                        "options": ["rwnd (Receive Window)", "cwnd (Congestion Window)", "MSS (Maximum Segment Size)", "SSTHRESH"],
                        "answer": "rwnd (Receive Window)",
                        "explanation": "The rwnd field reflects the currently free buffer space in the receiver's TCP socket buffer.",
                        "source_snippet": "Unit 5, Section 3.1: Sliding window flow control buffer management.",
                    },
                ],
            },
            {
                "name": "TCP Congestion Control (Reno, Cubic)",
                "keywords": ["Slow Start", "AIMD", "Fast Retransmit", "Fast Recovery", "cwnd", "ssthresh"],
                "summary": "Additive Increase Multiplicative Decrease (AIMD), duplicate ACK handling, and loss recovery phases.",
                "difficulty_prior": 0.55,
                "initial_mastery": 0.35,  # WEAK TOPIC!
                "attempts": 8,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "hard",
                        "bloom": "analyze",
                        "stem": "In TCP Tahoe/Reno, what triggers Fast Retransmit before the retransmission timeout timer expires?",
                        "options": [
                            "Arrival of 3 duplicate ACKs",
                            "Arrival of a single NACK",
                            "Reaching cwnd = ssthresh",
                            "Expiration of the round-trip timer",
                        ],
                        "answer": "Arrival of 3 duplicate ACKs",
                        "explanation": "Receiving 3 identical duplicate ACKs strongly signals that a specific segment was lost while subsequent ones arrived.",
                        "source_snippet": "Unit 5, Section 4.2: Fast Retransmit and Fast Recovery state transitions.",
                    },
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "apply",
                        "stem": "During TCP's Slow Start phase, by how much does the congestion window (cwnd) grow upon receipt of each ACK?",
                        "options": [
                            "It doubles every Round Trip Time (RTT)",
                            "It increases linearly by 1 MSS per RTT",
                            "It remains strictly constant",
                            "It halves upon each ACK",
                        ],
                        "answer": "It doubles every Round Trip Time (RTT)",
                        "explanation": "Despite the name 'Slow Start', cwnd increases by 1 MSS for every received ACK, resulting in exponential doubling every RTT.",
                        "source_snippet": "Unit 5, Section 4.1: Slow Start exponential ramp-up.",
                    },
                ],
            },
        ],
    },
    {
        "unit": "Unit 6: Application Layer",
        "summary": "Core internet protocols: DNS resolution, Web HTTP/2/3, SMTP email delivery, and cryptographic TLS handshakes.",
        "topics": [
            {
                "name": "Domain Name System (DNS)",
                "keywords": ["Root Servers", "TLD", "Authoritative", "A Record", "CNAME", "Port 53"],
                "summary": "Hierarchical distributed name resolution mapping human-readable domain names to numerical IP addresses.",
                "difficulty_prior": 0.32,
                "initial_mastery": 0.93,
                "attempts": 7,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "Which well-known transport port number is predominantly used by standard DNS queries?",
                        "options": ["Port 53", "Port 80", "Port 443", "Port 25"],
                        "answer": "Port 53",
                        "explanation": "DNS runs over UDP (and TCP for zone transfers or large responses) on port 53.",
                        "source_snippet": "Unit 6, Section 1.1: DNS server ports and query formats.",
                    },
                ],
            },
            {
                "name": "HTTP/HTTPS & Web Protocols",
                "keywords": ["HTTP/1.1", "HTTP/2", "HTTP/3", "QUIC", "REST", "Stateless", "Status Codes"],
                "summary": "Hypertext transfer protocol evolution from pipelining to multiplexed binary frames and UDP-based QUIC.",
                "difficulty_prior": 0.36,
                "initial_mastery": 0.86,
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "What underlying transport protocol does HTTP/3 utilize instead of standard TCP?",
                        "options": ["QUIC (over UDP)", "SCTP", "Raw IP", "TLS over TCP"],
                        "answer": "QUIC (over UDP)",
                        "explanation": "HTTP/3 uses QUIC built on UDP to eliminate head-of-line blocking at the transport layer.",
                        "source_snippet": "Unit 6, Section 2.3: HTTP/3 and QUIC transport multiplexing.",
                    },
                ],
            },
            {
                "name": "Email Protocols (SMTP, IMAP, POP3)",
                "keywords": ["MTA", "MUA", "Mailbox", "Push vs Pull", "Port 25", "Port 993"],
                "summary": "Store-and-forward message routing via SMTP push and client mailbox access via IMAP/POP3 pull.",
                "difficulty_prior": 0.35,
                "initial_mastery": 0.89,
                "attempts": 4,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "easy",
                        "bloom": "remember",
                        "stem": "Which protocol is utilized to transfer email messages between Mail Transfer Agents (MTAs) across servers?",
                        "options": ["SMTP (Simple Mail Transfer Protocol)", "POP3", "IMAP4", "SNMP"],
                        "answer": "SMTP (Simple Mail Transfer Protocol)",
                        "explanation": "SMTP is the standard protocol for sending/pushing mail from client to server and server to server.",
                        "source_snippet": "Unit 6, Section 3.1: SMTP message architecture.",
                    },
                ],
            },
            {
                "name": "Network Security & TLS/SSL",
                "keywords": ["Symmetric Key", "Asymmetric Key", "Certificates", "CA", "AES", "RSA", "Handshake"],
                "summary": "Confidentiality, message integrity, cryptographic signatures, public-key infrastructure, and TLS records.",
                "difficulty_prior": 0.48,
                "initial_mastery": 0.76,
                "attempts": 5,
                "questions": [
                    {
                        "type": "mcq",
                        "difficulty": "medium",
                        "bloom": "understand",
                        "stem": "In the TLS 1.3 cryptographic handshake, what mechanism generates the temporary symmetric session keys?",
                        "options": [
                            "Diffie-Hellman Key Exchange (ECDHE)",
                            "Static RSA encryption of premaster secret",
                            "MD5 hashing of client random",
                            "DES cipher block chaining",
                        ],
                        "answer": "Diffie-Hellman Key Exchange (ECDHE)",
                        "explanation": "TLS 1.3 exclusively mandates Ephemeral Diffie-Hellman to guarantee Forward Secrecy.",
                        "source_snippet": "Unit 6, Section 4.2: TLS 1.3 key exchange and cipher suites.",
                    },
                ],
            },
        ],
    },
]


def seed_database(db: Session = None):
    """Seed the database with users, badges, sample syllabus, questions, and demo mastery."""
    own_db = False
    if db is None:
        db = SessionLocal()
        own_db = True

    try:
        # 1. Ensure table schema exists
        Base.metadata.create_all(bind=engine)

        # 2. Ensure badge catalog exists
        _ensure_badges(db)

        # 3. Create or get Demo User
        demo_user = db.query(User).filter(User.email == "demo@quizforge.app").first()
        if not demo_user:
            demo_user = User(
                email="demo@quizforge.app",
                name="Alex Demo",
                password_hash=get_password_hash("demo1234"),
                role="student",
                is_active=True,
            )
            db.add(demo_user)
            db.flush()
            logger.info("Created Demo Student: demo@quizforge.app / demo1234")

        # 4. Create or get Faculty User
        faculty_user = db.query(User).filter(User.email == "faculty@quizforge.app").first()
        if not faculty_user:
            faculty_user = User(
                email="faculty@quizforge.app",
                name="Prof. Sharma (ISE Dept)",
                password_hash=get_password_hash("faculty1234"),
                role="faculty",
                is_active=True,
            )
            db.add(faculty_user)
            db.flush()
            logger.info("Created Faculty: faculty@quizforge.app / faculty1234")

        # 5. UserStats for Demo User
        stats = db.query(UserStats).filter(UserStats.user_id == demo_user.id).first()
        if not stats:
            stats = UserStats(
                user_id=demo_user.id,
                xp=1250,
                level=4,
                streak=3,
                longest_streak=5,
                streak_freeze=1,
                last_active=datetime.utcnow(),
                total_quizzes=6,
                total_correct=38,
                total_attempts=46,
            )
            db.add(stats)
            db.flush()

        # 6. Sample Syllabus Document: "Computer Networks (BIS586)"
        doc = db.query(Document).filter(Document.filename == "computer_networks_bis586.pdf").first()
        if not doc:
            doc = Document(
                user_id=demo_user.id,
                filename="computer_networks_bis586.pdf",
                original_filename="Computer Networks (Course Code: BIS586).pdf",
                file_size=1024 * 1024 * 3,  # 3 MB
                mime_type="application/pdf",
                status="ready",
                page_count=28,
                raw_text="Bangalore Institute of Technology. Department of Information Science & Engineering. Computer Networks Syllabus...",
                structure_json=json.dumps([{"unit": u["unit"]} for u in COMPUTER_NETWORKS_UNITS]),
            )
            db.add(doc)
            db.flush()
            logger.info("Created Document: computer_networks_bis586.pdf")

        # 7. Create Topics & Questions
        topic_count = 0
        question_count = 0
        for u_idx, unit_data in enumerate(COMPUTER_NETWORKS_UNITS, start=1):
            # Unit root topic
            unit_topic = (
                db.query(Topic)
                .filter(Topic.document_id == doc.id, Topic.name == unit_data["unit"])
                .first()
            )
            if not unit_topic:
                unit_topic = Topic(
                    document_id=doc.id,
                    parent_id=None,
                    name=unit_data["unit"],
                    keywords=json.dumps(["unit", "networking", f"unit_{u_idx}"]),
                    summary=unit_data["summary"],
                    difficulty_prior=0.4,
                    order_index=u_idx * 10,
                )
                db.add(unit_topic)
                db.flush()
                topic_count += 1

            for t_idx, topic_data in enumerate(unit_data["topics"], start=1):
                subtopic = (
                    db.query(Topic)
                    .filter(Topic.document_id == doc.id, Topic.name == topic_data["name"])
                    .first()
                )
                if not subtopic:
                    subtopic = Topic(
                        document_id=doc.id,
                        parent_id=unit_topic.id,
                        name=topic_data["name"],
                        keywords=json.dumps(topic_data["keywords"]),
                        summary=topic_data["summary"],
                        difficulty_prior=topic_data["difficulty_prior"],
                        order_index=u_idx * 10 + t_idx,
                    )
                    db.add(subtopic)
                    db.flush()
                    topic_count += 1

                # Questions for this subtopic
                for q_data in topic_data["questions"]:
                    existing_q = (
                        db.query(Question)
                        .filter(Question.topic_id == subtopic.id, Question.stem == q_data["stem"])
                        .first()
                    )
                    if not existing_q:
                        q_obj = Question(
                            topic_id=subtopic.id,
                            type=q_data["type"],
                            difficulty=q_data["difficulty"],
                            bloom=q_data["bloom"],
                            stem=q_data["stem"],
                            options=json.dumps(q_data["options"]) if q_data["options"] else None,
                            answer=q_data["answer"],
                            explanation=q_data["explanation"],
                            source_snippet=q_data["source_snippet"],
                            status="active",
                            time_limit_ms=30000,
                        )
                        db.add(q_obj)
                        question_count += 1

                # 8. Mastery for demo user on this subtopic
                mastery = (
                    db.query(Mastery)
                    .filter(Mastery.user_id == demo_user.id, Mastery.topic_id == subtopic.id)
                    .first()
                )
                p_L = topic_data.get("initial_mastery", 0.70)
                attempts_count = topic_data.get("attempts", 4)
                if not mastery:
                    history = []
                    curr_p = topic_data["difficulty_prior"]
                    for a_idx in range(attempts_count):
                        is_corr = curr_p < p_L or a_idx == attempts_count - 1
                        curr_p = min(0.98, max(0.20, curr_p + (0.12 if is_corr else -0.15)))
                        history.append({
                            "ts": (datetime.utcnow() - timedelta(days=attempts_count - a_idx)).isoformat(),
                            "p_L": round(curr_p, 3),
                            "correct": is_corr,
                        })
                    mastery = Mastery(
                        user_id=demo_user.id,
                        topic_id=subtopic.id,
                        p_L=p_L,
                        attempts_count=attempts_count,
                        history_json=json.dumps(history),
                        last_attempted_at=datetime.utcnow() - timedelta(hours=3),
                    )
                    db.add(mastery)

        # 9. Badges awarded to demo user
        badges_to_award = ["first_question", "first_correct", "streak_3", "speed_demon"]
        for b_code in badges_to_award:
            b_obj = db.query(Badge).filter(Badge.code == b_code).first()
            if b_obj:
                has_ub = (
                    db.query(UserBadge)
                    .filter(UserBadge.user_id == demo_user.id, UserBadge.badge_id == b_obj.id)
                    .first()
                )
                if not has_ub:
                    ub = UserBadge(user_id=demo_user.id, badge_id=b_obj.id, earned_at=datetime.utcnow() - timedelta(days=1))
                    db.add(ub)

        # 10. Sample quiz session for demo user
        session = (
            db.query(QuizSession)
            .filter(QuizSession.user_id == demo_user.id)
            .first()
        )
        if not session:
            session = QuizSession(
                user_id=demo_user.id,
                document_id=doc.id,
                mode="adaptive",
                status="completed",
                score=0.85,
                xp_earned=140,
                max_questions=10,
                attempt_count=10,
                correct_count=8,
                started_at=datetime.utcnow() - timedelta(hours=2),
                completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
            )
            db.add(session)

        db.commit()
        logger.info(f"Database seeded successfully! Topics created: {topic_count}, Questions created: {question_count}")

    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to seed database: {e}")
        raise
    finally:
        if own_db:
            db.close()


if __name__ == "__main__":
    seed_database()
