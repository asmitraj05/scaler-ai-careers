def create_hello_world_pdf(filename="hello_world.pdf"):
    # Raw PDF built by hand — no external libraries required.
    # All byte offsets in the xref table must be exact.

    text = "Hello World"

    # Build each object as a byte string so we can track exact offsets.
    header = b"%PDF-1.4\n"

    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"

    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"

    obj3 = (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R\n"
        b"   /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R\n"
        b"   /Resources << /Font << /F1 5 0 R >> >> >>\n"
        b"endobj\n"
    )

    stream_content = (
        f"BT\n"
        f"/F1 48 Tf\n"
        f"220 396 Td\n"
        f"({text}) Tj\n"
        f"ET"
    ).encode()

    obj4 = (
        b"4 0 obj\n"
        b"<< /Length " + str(len(stream_content)).encode() + b" >>\n"
        b"stream\n" +
        stream_content +
        b"\nendstream\n"
        b"endobj\n"
    )

    obj5 = (
        b"5 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\n"
        b"endobj\n"
    )

    # Calculate byte offsets for xref table
    off1 = len(header)
    off2 = off1 + len(obj1)
    off3 = off2 + len(obj2)
    off4 = off3 + len(obj3)
    off5 = off4 + len(obj4)
    xref_offset = off5 + len(obj5)

    xref = (
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n" +
        f"{off1:010d} 00000 n \n".encode() +
        f"{off2:010d} 00000 n \n".encode() +
        f"{off3:010d} 00000 n \n".encode() +
        f"{off4:010d} 00000 n \n".encode() +
        f"{off5:010d} 00000 n \n".encode()
    )

    trailer = (
        b"trailer\n"
        b"<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n" +
        str(xref_offset).encode() +
        b"\n%%EOF\n"
    )

    with open(filename, "wb") as f:
        f.write(header + obj1 + obj2 + obj3 + obj4 + obj5 + xref + trailer)

    print(f"PDF created: {filename}")


if __name__ == "__main__":
    create_hello_world_pdf()
