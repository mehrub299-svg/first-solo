import pytest

from app.services.chunking import ChunkingService


def test_empty_text_gives_no_chunks():
    service = ChunkingService(chunk_size=200, overlap=40)
    assert service.split("") == []
    assert service.split("   \n  ") == []


def test_short_text_is_one_chunk():
    assert ChunkingService(chunk_size=200, overlap=40).split("short text") == ["short text"]


def test_nul_characters_are_removed():
    assert ChunkingService(chunk_size=200, overlap=40).split("a\x00b") == ["ab"]


def test_chunks_respect_size_and_overlap():
    service = ChunkingService(chunk_size=200, overlap=40)
    text = " ".join(f"Sentence number {i} is here." for i in range(100))
    chunks = service.split(text)

    assert len(chunks) > 5
    assert all(0 < len(chunk) <= 200 for chunk in chunks)
    assert chunks[0].startswith("Sentence number 0")
    assert chunks[-1].endswith("Sentence number 99 is here.")
    for previous, following in zip(chunks, chunks[1:]):
        assert previous.split()[-1] in following, "consecutive chunks do not overlap"


def test_invalid_overlap_is_rejected():
    with pytest.raises(ValueError):
        ChunkingService(chunk_size=100, overlap=60)