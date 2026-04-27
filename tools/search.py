import re
import requests
import base64
from urllib.parse import urlparse

from state import AgentState
from config import SEARXNG_URL, SEARXNG_TIMEOUT, SEARXNG_HEADERS, llm


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text


def _get_source_name(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host.replace("www.", "")
    except Exception:
        return ""


def _normalize_results(raw_results: list) -> list:
    normalized = []
    seen_urls = set()

    for item in raw_results:
        url = _clean_text(item.get("url") or item.get("link") or "")
        title = _clean_text(item.get("title") or "")
        snippet = _clean_text(
            item.get("content")
            or item.get("snippet")
            or item.get("description")
            or ""
        )

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        normalized.append({
            "title": title if title else url,
            "url": url,
            "snippet": snippet,
            "source": _get_source_name(url),
        })

    return normalized


def _format_links(query: str, results: list) -> str:
    lines = [f"Berikut beberapa sumber untuk topik: {query}\n"]

    for i, item in enumerate(results[:7], 1):
        lines.append(f"{i}. {item['title']}")
        lines.append(f"   {item['url']}")
        if item["snippet"]:
            lines.append(f"   {item['snippet']}")
        lines.append("")

    return "\n".join(lines).strip()


def _remove_raw_urls(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fallback_answer(query: str, results: list, mode: str) -> str:
    snippets = [item["snippet"] for item in results[:5] if item.get("snippet")]
    sources = [item["source"] for item in results[:5] if item.get("source")]

    if mode == "news":
        if snippets:
            joined = " ".join(snippets[:2])
            return (
                f"Berdasarkan hasil pencarian saat ini, perkembangan terbaru terkait {query} "
                f"mengarah pada hal berikut: {joined}"
            )
        return f"Berdasarkan hasil pencarian saat ini, ada perkembangan terkait {query}, tetapi detail ringkasnya belum cukup jelas."

    if snippets:
        joined = " ".join(snippets[:2])
        source_text = f" Sumber yang diringkas antara lain: {', '.join(dict.fromkeys(sources))}." if sources else ""
        return f"Berdasarkan hasil pencarian saat ini, {joined}{source_text}"

    return f"Saya menemukan beberapa hasil terkait {query}, tetapi ringkasannya belum cukup jelas untuk dijawab dengan yakin."


def _generate_natural_answer(user_input: str, query: str, mode: str, results: list) -> str:
    context_blocks = []

    for i, item in enumerate(results[:5], 1):
        snippet_text = item['snippet']
        if len(snippet_text) > 250:
            snippet_text = snippet_text[:250] + "..."
        context_blocks.append(
            f"[{i}]\n"
            f"Judul: {item['title']}\n"
            f"Sumber: {item['source']}\n"
            f"Ringkasan: {item['snippet']}\n"
        )

    context = "\n".join(context_blocks)

    prompt = f"""
Anda adalah Aira, asisten AI berbahasa Indonesia.

Tugas Anda:
- Jawab pertanyaan pengguna secara natural, komprehensif, mendetail, akurat, dan to the point.
- WAJIB gunakan minimal 2 atau 3 paragraf untuk menjelaskan topik secara mendalam.
- Jika ada banyak informasi, susun menggunakan poin-poin (bullet points) agar rapi dan informatif.
- Gunakan data hasil pencarian web yang diberikan di bawah ini.
- Dilarang mengarang informasi (halusinasi).
- Jangan tampilkan daftar link mentah, URL, atau format seperti mesin pencari, KECUALI pengguna secara eksplisit meminta link.
- Jangan membuka jawaban dengan kalimat seperti "Hasil pencarian untuk:".

Mode jawaban: {mode}
Pertanyaan pengguna: {user_input}
Query pencarian: {query}

Data web:
{context}

Berikan jawaban langsung tanpa kalimat pembuka yang bertele-tele.
"""

    try:
        response = llm.invoke(prompt)
        text = getattr(response, "content", str(response)).strip()

        if not text:
            return _fallback_answer(query, results, mode)

        if mode != "links":
            text = _remove_raw_urls(text)

        return text if text else _fallback_answer(query, results, mode)

    except Exception:
        return _fallback_answer(query, results, mode)


def execute_search(state: AgentState):
    user_input = state.get("user_input", "").strip()
    query = state.get("search_query", "").strip()
    mode = state.get("search_mode", "answer").strip().lower() or "answer"

    if not query:
        return {"final_answer": "Query kosong, tidak bisa mencari."}

    category = "images" if mode == "images" else "general"

    try:
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": query,
                "format": "json",
                "language": "id-ID",
                "safesearch": 1,
                "categories": category
            },
            headers=SEARXNG_HEADERS,
            timeout=SEARXNG_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        raw_results = data.get("results", [])
        
        if mode == "images":
            if raw_results:
                image_url = ""
                for item in raw_results:
                    candidate_url = item.get("img_src") or item.get("thumbnail") or ""
                    
                    if not candidate_url:
                        continue

                    if candidate_url.lower().endswith((".svg", ".ico")):
                        continue
                        
                    if candidate_url.startswith("//"):
                        candidate_url = "https:" + candidate_url
                        
                    if candidate_url.startswith("http"):
                        try:
                            img_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                            img_res = requests.get(candidate_url, headers=img_headers, timeout=5)
                            
                            if img_res.status_code == 200:
                                content_type = img_res.headers.get('Content-Type', '').lower()

                                if 'text/' in content_type or 'html' in content_type or 'svg' in content_type:
                                    continue 
                                    
                                if not content_type:
                                    content_type = 'image/jpeg' 
                                
                                base64_encoded = base64.b64encode(img_res.content).decode('utf-8')
                                image_url = f"data:{content_type};base64,{base64_encoded}"
                                
                                break 
                        except:
                            continue
                            
                if image_url:
                    return {
                        "search_results": raw_results[:2],
                        "final_answer": f"🖼️ Berikut adalah gambar dari internet untuk: {query}",
                        "image_url": image_url 
                    }
                    
            return {
                "search_results": [],
                "final_answer": f"Maaf, saya tidak menemukan gambar yang bisa diakses untuk: {query}"
            }
        results = _normalize_results(raw_results)[:7]

        if not results:
            return {
                "search_results": [],
                "final_answer": f"Saya belum menemukan hasil yang relevan untuk: {query}"
            }

        if mode == "links":
            final_answer = _format_links(query, results)

        elif mode == "news":
            final_answer = _format_links(query, results) 
            final_answer = final_answer.replace("Berikut beberapa sumber", "Berikut adalah berita terkini")

        else:
            final_answer = _generate_natural_answer(user_input, query, "answer", results)

        return {
            "search_results": results,
            "final_answer": final_answer
        }

    except requests.exceptions.RequestException as e:
        return {"final_answer": f"Maaf, mesin pencarian sedang tidak dapat dihubungi. Coba lagi sebentar lagi. Search gagal: {str(e)}"}
    except ValueError:
        return {"final_answer": "Search gagal: respons bukan JSON yang valid."}
    except Exception as e:
        return {"final_answer": f"Search gagal: {str(e)}"}