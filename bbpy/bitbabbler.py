import time
from typing import Optional

from .ftdi import (
    FTDIDevice,
    FTDI_VENDOR_ID,
    MPSSE_DATA_BYTE_IN_POS_MSB,
    MPSSE_NO_ADAPTIVE_CLK,
    MPSSE_NO_CLK_DIV5,
    MPSSE_NO_LOOPBACK,
    MPSSE_NO_3PHASE_CLK,
    MPSSE_SEND_IMMEDIATE,
    MPSSE_SET_CLK_DIVISOR,
    MPSSE_SET_DATABITS_HIGH,
    MPSSE_SET_DATABITS_LOW,
)


BB_VENDOR_ID = FTDI_VENDOR_ID
BB_PRODUCT_ID = 0x7840


def real_bitrate(bitrate: int) -> int:
    if bitrate >= 30_000_000:
        return 30_000_000
    if bitrate <= 458:
        return 458
    return 30_000_000 // (30_000_000 // bitrate)


def fold_bytes(data: bytes, folds: int) -> bytes:
    if folds <= 0:
        return bytes(data)
    if len(data) & ((1 << folds) - 1):
        raise ValueError(f"input length {len(data)} is not divisible by 2**{folds}")
    b = bytearray(data)
    length = len(b)
    for _ in range(folds):
        half = length // 2
        # xor second half into first half
        for i in range(half):
            b[i] ^= b[half + i]
        length = half
    return bytes(b[:length])


class BitBabbler(FTDIDevice):
    def __init__(self, ftdi: FTDIDevice, bitrate: Optional[int] = None, latency_ms: Optional[int] = None,
                 enable_mask: int = 0x0F, disable_polarity: int = 0x00) -> None:
        super().__init__(ftdi.dev, ftdi.in_ep, ftdi.out_ep, ftdi.wMaxPacketSize, ftdi.interface_index, ftdi.timeout_ms)
        self.bitrate = real_bitrate(bitrate or 2_500_000)
        # mirror C++ transformation
        self._enable_mask = (~enable_mask << 4) & 0xF0
        self._disable_pol = (disable_polarity << 4) & 0xF0
        # choose latency: ceil(packet_time_ms) + 2, clamped 1..255, allow override
        packet_ms = (self.wMaxPacketSize * 8000) / self.bitrate
        default_latency = max(1, min(255, int(packet_ms) + 2))
        self.latency_ms = latency_ms if latency_ms is not None else default_latency

    @staticmethod
    def open(serial: Optional[str] = None) -> "BitBabbler":
        base = FTDIDevice.find(BB_VENDOR_ID, BB_PRODUCT_ID, serial=serial)
        if base is None:
            raise RuntimeError("BitBabbler device not found (vendor 0x0403, product 0x7840)")
        bb = BitBabbler(base)
        if not bb.init():
            raise RuntimeError("Failed to initialize BitBabbler (MPSSE sync)")
        return bb

    def init(self) -> bool:
        if not self.init_mpsse(self.latency_ms):
            return False
        # device-specific init
        clk_div = 30_000_000 // self.bitrate - 1
        cmd = bytes([
            MPSSE_NO_CLK_DIV5,
            MPSSE_NO_ADAPTIVE_CLK,
            MPSSE_NO_3PHASE_CLK,
            MPSSE_SET_DATABITS_LOW,
            0x00 | self._disable_pol,         # levels (CLK, DO, CS low)
            0x0B | self._enable_mask,         # directions (CLK, DO, CS outputs)
            MPSSE_SET_DATABITS_HIGH,
            0x00,
            0x00,
            MPSSE_SET_CLK_DIVISOR,
            (clk_div & 0xFF),
            ((clk_div >> 8) & 0xFF),
            MPSSE_NO_LOOPBACK,
        ])
        self.write(cmd)
        time.sleep(0.030)
        # purge any residual data
        try:
            _ = self._read_raw(self.wMaxPacketSize)
        except Exception:
            pass
        return True

    def read_entropy(self, nbytes: int) -> bytes:
        if nbytes < 1 or nbytes > 65536:
            raise ValueError("nbytes must be 1..65536")
        # Build MPSSE read bytes command (MSB, pos edge)
        cmd = bytes([
            MPSSE_DATA_BYTE_IN_POS_MSB,
            (nbytes - 1) & 0xFF,
            ((nbytes - 1) >> 8) & 0xFF,
            MPSSE_SEND_IMMEDIATE,
        ])
        self.write(cmd)
        return self.read_data(nbytes)

    def read_entropy_folded(self, out_len: int, folds: int) -> bytes:
        if folds <= 0:
            return self.read_entropy(out_len)
        out = bytearray()
        remain = out_len
        # Each chunk we read raw_len = chunk_out << folds, keeping raw_len <= 65536
        while remain > 0:
            max_out_per_read = max(1, min(remain, 65536 >> folds))
            raw_len = max_out_per_read << folds
            raw = self.read_entropy(raw_len)
            folded = fold_bytes(raw, folds)
            out.extend(folded)
            remain -= len(folded)
        return bytes(out)
