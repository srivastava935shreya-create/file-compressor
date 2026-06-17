"""
================================================================================
HUFFMAN CODING FILE COMPRESSION SYSTEM (DSA MINI-PROJECT)
================================================================================
A simple, beginner-friendly implementation of Huffman Coding in Python.

DATA STRUCTURES USED:
1. BINARY TREES:
   - Used to construct the Huffman Tree. Leaf nodes store unique byte values, and
     internal nodes store combined frequencies of their children.
   - Traversing the tree (left = '0', right = '1') generates prefix codes.
2. PRIORITY QUEUES (using heapq):
   - Used to efficiently select the two nodes with the lowest frequencies.
   - Allows bottom-up construction of the Huffman Tree in O(N log N) time.

FILE COMPRESSION MECHANICS:
- Works at the raw byte level (0-255) to compress any file type (text, images, etc.)
- Writes to binary files with a custom format:
  [4-byte JSON size] [1-byte padding bit count] [JSON Frequency Table] [Packed Bits]
================================================================================
"""

import collections
import heapq
import os
import json

class HuffmanNode:
    """Represents a node in the Huffman Tree."""
    def __init__(self, char, freq, left=None, right=None):
        self.char = char  # Byte value (0-255) (None for internal nodes)
        self.freq = freq  # frequency of the byte value
        self.left = left  # left child
        self.right = right  # right child

    def is_leaf(self):
        return self.left is None and self.right is None

    def __lt__(self, other):
        # Comparison based on frequency for priority queue (min-heap) sorting
        return self.freq < other.freq

def build_tree(freq_map):
    """Builds the Huffman tree from byte frequencies and returns the root."""
    # Initialize heap with leaf nodes
    heap = [HuffmanNode(char, freq) for char, freq in freq_map.items()]
    heapq.heapify(heap)

    # Edge case: only one unique byte value
    if len(heap) == 1:
        node = heapq.heappop(heap)
        return HuffmanNode(None, node.freq, left=node)

    # Merge nodes until only the root remains
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq, left, right)
        heapq.heappush(heap, merged)

    return heap[0] if heap else None

def generate_codes(root):
    """Traverses the tree to generate binary codes for each byte value."""
    codes = {}
    def traverse(node, current_code):
        if not node:
            return
        if node.is_leaf():
            codes[node.char] = current_code
            return
        traverse(node.left, current_code + "0")
        traverse(node.right, current_code + "1")

    traverse(root, "")
    return codes

def compress(data, codes):
    """Encodes the input bytes into a binary string representation."""
    return "".join(codes[byte] for byte in data)

def decompress(encoded_text, root):
    """Decodes the binary string back to original bytes by traversing the tree."""
    if not root:
        return b""
    decoded_bytes = bytearray()
    current = root
    for bit in encoded_text:
        current = current.left if bit == "0" else current.right
        if current.is_leaf():
            decoded_bytes.append(current.char)
            current = root
    return bytes(decoded_bytes)

def run_interactive_demo():
    """Interactive demo to compress and decompress raw text entered in terminal."""
    text = input("\nEnter text to compress: ").strip()
    if not text:
        print("Error: Input text cannot be empty!")
        return

    data = text.encode('utf-8')
    freq_map = collections.Counter(data)
    root = build_tree(freq_map)
    codes = generate_codes(root)
    encoded_text = compress(data, codes)
    decoded_bytes = decompress(encoded_text, root)
    decoded_text = decoded_bytes.decode('utf-8', errors='replace')

    # Size calculation
    original_size = len(data) * 8
    compressed_size = len(encoded_text)
    ratio = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0

    print("\n" + "=" * 60)
    print("                    COMPRESSION RESULTS")
    print("=" * 60)
    print(f"Original Text        : \"{text}\"")
    print(f"Encoded Binary String: {encoded_text}")
    print(f"Decoded Text         : \"{decoded_text}\"")
    
    print("\n" + "-" * 60)
    print("                         METRICS")
    print("-" * 60)
    print(f"Original Size        : {original_size} bits ({len(data)} bytes)")
    print(f"Compressed Size      : {compressed_size} bits")
    print(f"Compression Saved    : {ratio:.2f}%")
    
    print("\nHuffman Codes Dictionary:")
    for byte_val, code in sorted(codes.items(), key=lambda x: len(x[1])):
        # Represent byte as printable character or integer
        char_repr = repr(chr(byte_val)) if 32 <= byte_val <= 126 else f"Byte {byte_val}"
        print(f"  {char_repr:<10} : {code}")
    print("=" * 60 + "\n")

def run_file_compression():
    """Compresses a physical file into a packed Huffman binary file."""
    input_path = input("\nEnter the path of the file to compress: ").strip()
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    output_path = input_path + ".huff"
    with open(input_path, 'rb') as f:
        data = f.read()

    if not data:
        print("Error: File is empty.")
        return

    freq_map = collections.Counter(data)
    root = build_tree(freq_map)
    codes = generate_codes(root)
    encoded_text = compress(data, codes)

    # Padding to make bitstring length a multiple of 8
    padding_length = (8 - (len(encoded_text) % 8)) % 8
    padded_encoded_text = encoded_text + ("0" * padding_length)

    # Convert bitstring to actual bytes
    byte_arr = bytearray()
    for i in range(0, len(padded_encoded_text), 8):
        byte_arr.append(int(padded_encoded_text[i:i+8], 2))

    # Serialize metadata header
    metadata_bytes = json.dumps(freq_map).encode('utf-8')

    # Write: [4-byte metadata length] [1-byte padding length] [metadata] [compressed bytes]
    with open(output_path, 'wb') as f:
        f.write(len(metadata_bytes).to_bytes(4, byteorder='big'))
        f.write(padding_length.to_bytes(1, byteorder='big'))
        f.write(metadata_bytes)
        f.write(byte_arr)

    orig_size = os.path.getsize(input_path)
    comp_size = os.path.getsize(output_path)
    saving = ((orig_size - comp_size) / orig_size) * 100 if orig_size > 0 else 0

    print(f"\n[Success] Compressed successfully!")
    print(f"  Original File   : {input_path} ({orig_size} bytes)")
    print(f"  Compressed File : {output_path} ({comp_size} bytes)")
    print(f"  Physical Savings: {saving:.2f}%")

def run_file_decompression():
    """Decompresses a packed Huffman binary file back to its original state."""
    input_path = input("\nEnter the path of the compressed (.huff) file: ").strip()
    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    output_path = input_path.replace(".huff", "")
    if output_path == input_path:
        output_path += "_decompressed"
    else:
        output_path = output_path.rsplit('.', 1)[0] + "_recovered." + output_path.rsplit('.', 1)[-1]

    with open(input_path, 'rb') as f:
        # Read header sizes
        metadata_len_bytes = f.read(4)
        padding_len_bytes = f.read(1)
        if len(metadata_len_bytes) < 4 or not padding_len_bytes:
            print("Error: Invalid compressed file format.")
            return

        metadata_len = int.from_bytes(metadata_len_bytes, byteorder='big')
        padding_len = int.from_bytes(padding_len_bytes, byteorder='big')

        # Read frequency metadata
        metadata_bytes = f.read(metadata_len)
        raw_freq_map = json.loads(metadata_bytes.decode('utf-8'))
        # Convert JSON string keys back to int byte values
        freq_map = {int(k): v for k, v in raw_freq_map.items()}

        # Read payload
        compressed_bytes = f.read()

    # Convert bytes back to bitstring
    bit_string = "".join(f"{b:08b}" for b in compressed_bytes)
    if padding_len > 0:
        bit_string = bit_string[:-padding_len]

    # Reconstruct tree and decompress
    root = build_tree(freq_map)
    decoded_bytes = decompress(bit_string, root)

    with open(output_path, 'wb') as f:
        f.write(decoded_bytes)

    print(f"\n[Success] Decompressed successfully!")
    print(f"  Recovered File: {output_path} ({os.path.getsize(output_path)} bytes)")

def main():
    while True:
        print("=" * 60)
        print("         Huffman Coding Compression System (DSA Project)      ")
        print("=" * 60)
        print("  1. Compress Interactive Text (Terminal Demo)")
        print("  2. Compress File (Disk Read/Write)")
        print("  3. Decompress File (Disk Read/Write)")
        print("  4. Exit")
        print("-" * 60)
        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            run_interactive_demo()
        elif choice == "2":
            run_file_compression()
        elif choice == "3":
            run_file_decompression()
        elif choice == "4":
            print("\nExiting. Goodbye!")
            break
        else:
            print("\nError: Invalid choice. Please select 1-4.\n")

if __name__ == "__main__":
    main()
