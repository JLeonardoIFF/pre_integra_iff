# --------------------------------------------------
# Arquivo: supabase_db.py  (versão atualizada)
# --------------------------------------------------
import json
import re
import streamlit as st
from supabase import create_client


def get_db():
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _to_bool(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    if isinstance(v, (int, float)):
        return bool(int(v))
    if isinstance(v, str):
        return v.lower() in ("1", "true", "t", "yes", "y")
    return False


def sanitize_key(s: str) -> str:
    # mesma lógica usada no frontend para garantir consistência
    return re.sub(r'\W+', '_', str(s)).strip('_')


def load_progress_all(user_id):
    """
    Carrega progress_item (com check_* e nivel se existirem) e também user_progress.checks_map.
    Retorna: (geral:int, tema_map:dict, items:list)
    Garante que cada item contenha 'tema_key' já sanitizado.
    """
    supabase = get_db()
    # 1) tenta pegar progress_item com campos extras
    try:
        resp = supabase.table("progress_item") \
            .select("materia,tema_key,descr_idx,descritor,progress,check_teoria,check_resumo,check_questao,check_revisao,nivel") \
            .eq("user_id", user_id).execute()
    except Exception as e:
        st.warning(f"load_progress_all: fallback - não encontrou colunas extras em progress_item: {e}")
        try:
            resp = supabase.table("progress_item") \
                .select("materia,tema_key,descr_idx,descritor,progress") \
                .eq("user_id", user_id).execute()
        except Exception as e2:
            st.error(f"load_progress_all: erro ao consultar progress_item: {e2}")
            return 0, {}, []

    raw_items = getattr(resp, "data", None) or resp.data or []
    items = []
    for it in raw_items:
        if not isinstance(it, dict):
            continue
        # garante chaves
        it.setdefault("materia", "")
        it.setdefault("tema_key", "")
        it.setdefault("descr_idx", 0)
        it.setdefault("descritor", "")
        it.setdefault("progress", 0)
        it.setdefault("check_teoria", False)
        it.setdefault("check_resumo", False)
        it.setdefault("check_questao", False)
        it.setdefault("check_revisao", False)
        it.setdefault("nivel", "N/A")

        # sanitize tema_key para evitar mismatch com frontend
        raw_tk = it.get("tema_key") or f"{it.get('materia','')}__{it.get('descritor','')}"
        it["tema_key"] = sanitize_key(raw_tk)

        try:
            it["descr_idx"] = int(it["descr_idx"])
        except Exception:
            it["descr_idx"] = 0
        try:
            it["progress"] = int(it["progress"])
        except Exception:
            it["progress"] = 0
        it["check_teoria"] = _to_bool(it.get("check_teoria"))
        it["check_resumo"] = _to_bool(it.get("check_resumo"))
        it["check_questao"] = _to_bool(it.get("check_questao"))
        it["check_revisao"] = _to_bool(it.get("check_revisao"))
        it["nivel"] = it.get("nivel", "N/A") or "N/A"
        items.append(it)

    # 2) tentar ler checks_map + tema_map/progress da tabela user_progress
    tema_map = {}
    geral = 0
    try:
        resp2 = supabase.table("user_progress").select("checks_map, tema_map, progress").eq("user_id", user_id).limit(1).execute()
        rows = getattr(resp2, "data", None) or resp2.data or []
        if rows:
            up = rows[0] or {}
            checks_map = up.get("checks_map") or {}
            if isinstance(checks_map, str):
                try:
                    checks_map = json.loads(checks_map)
                except Exception:
                    checks_map = {}
            # aplica overlay: para cada key em checks_map, sobreescreve fields do item correspondente
            if isinstance(checks_map, dict) and checks_map:
                for composite_key, val in checks_map.items():
                    if not isinstance(val, dict):
                        continue
                    try:
                        # sanitiza a parte do tema também, caso o armazenamento venha com variações
                        tk_raw, idx_s = composite_key.rsplit(":::", 1)
                        tk = sanitize_key(tk_raw)
                        d_idx = int(idx_s)
                    except Exception:
                        continue
                    # procurar item correspondente
                    for it in items:
                        if it.get("tema_key") == tk and int(it.get("descr_idx", 0)) == d_idx:
                            if "check_teoria" in val:
                                it["check_teoria"] = _to_bool(val.get("check_teoria"))
                            if "check_resumo" in val:
                                it["check_resumo"] = _to_bool(val.get("check_resumo"))
                            if "check_questao" in val:
                                it["check_questao"] = _to_bool(val.get("check_questao"))
                            if "check_revisao" in val:
                                it["check_revisao"] = _to_bool(val.get("check_revisao"))
                            if "nivel" in val:
                                it["nivel"] = val.get("nivel", it.get("nivel", "N/A")) or "N/A"
                            if "progress" in val:
                                try:
                                    it["progress"] = int(val.get("progress", it.get("progress", 0)))
                                except Exception:
                                    pass
                            break
            # se a row tem tema_map/progress, use como fonte de verdade para o topo
            tema_map_candidate = up.get("tema_map") or {}
            if isinstance(tema_map_candidate, str):
                try:
                    tema_map_candidate = json.loads(tema_map_candidate)
                except Exception:
                    tema_map_candidate = {}
            if isinstance(tema_map_candidate, dict) and tema_map_candidate:
                # sanitize keys of tema_map_candidate
                sanitized_tmap = {sanitize_key(k): int(v) for k, v in (tema_map_candidate.items())}
                tema_map = sanitized_tmap
                try:
                    geral = int(up.get("progress", 0))
                except Exception:
                    geral = 0
                return geral, tema_map, items
    except Exception as e:
        st.warning(f"load_progress_all: não foi possível ler user_progress (ignorado): {e}")

    # 3) fallback: recompute tema_map/geral a partir dos items
    counts = {}
    for it in items:
        tk = it.get("tema_key", "")
        tema_map[tk] = tema_map.get(tk, 0) + int(it.get("progress", 0))
        counts[tk] = counts.get(tk, 0) + 1
    for tk in list(tema_map.keys()):
        tema_map[tk] = int(tema_map[tk] / counts[tk]) if counts[tk] else 0
    geral = int(sum(tema_map.values()) / len(tema_map)) if tema_map else 0
    return geral, tema_map, items


def upsert_user_progress_cache(user_id, geral, tema_map, checks_map=None):
    """
    Forma determinística:
    - lê a linha user_progress (se existir)
    - mescla checks_map no checks_map existente
    - se existir row -> update, se não -> insert
    """
    supabase = get_db()
    # leitura explícita da linha existente
    existing_row = None
    try:
        resp = supabase.table("user_progress").select("*").eq("user_id", user_id).limit(1).execute()
        rows = getattr(resp, "data", None) or resp.data or []
        if rows:
            existing_row = rows[0] or {}
    except Exception as e:
        st.warning(f"upsert_user_progress_cache: falha ao ler user_progress: {e}")
        existing_row = None

    # pega checks_map existente em dict
    existing_checks = {}
    if existing_row:
        existing_checks = existing_row.get("checks_map") or {}
        if isinstance(existing_checks, str):
            try:
                existing_checks = json.loads(existing_checks)
            except Exception:
                existing_checks = {}
    # merged
    merged_checks = dict(existing_checks or {})
    if isinstance(checks_map, dict):
        for k, v in checks_map.items():
            # sanitize composite key antes de mesclar
            try:
                tk_raw, idx = k.rsplit(":::", 1)
                tk = sanitize_key(tk_raw)
                composite = f"{tk}:::{idx}"
            except Exception:
                composite = k
            merged_checks[composite] = v

    payload = {
        "user_id": user_id,
        "progress": int(geral),
        "tema_map": tema_map
    }
    # somente inclua checks_map se for dict (pode estar vazio)
    if isinstance(merged_checks, dict):
        payload["checks_map"] = merged_checks

    try:
        if existing_row:
            # update
            supabase.table("user_progress").update(payload).eq("user_id", user_id).execute()
            st.info("upsert_user_progress_cache: atualizou user_progress")
        else:
            # insert
            supabase.table("user_progress").insert(payload).execute()
            st.info("upsert_user_progress_cache: inseriu user_progress")
        return
    except Exception as e:
        # fallback: tentar upsert
        try:
            supabase.table("user_progress").upsert(payload).execute()
            st.info("upsert_user_progress_cache: upsert fallback executado")
            return
        except Exception as e2:
            st.error(f"upsert_user_progress_cache: falha ao gravar user_progress: {e2}")
            raise


def upsert_progress_item(user_id, materia, tema_key, descr_idx, descritor, progress, checks=None, nivel="N/A"):
    """
    Insere ou atualiza uma linha em progress_item para o descritor especificado.
    checks: dict com chaves booleanas: check_teoria, check_resumo, check_questao, check_revisao
    """
    supabase = get_db()
    descr_idx = int(descr_idx or 0)
    tk = sanitize_key(tema_key)
    payload = {
        "user_id": user_id,
        "materia": materia,
        "tema_key": tk,
        "descr_idx": descr_idx,
        "descritor": descritor,
        "progress": int(progress or 0),
        "nivel": nivel or "N/A"
    }
    if isinstance(checks, dict):
        payload["check_teoria"] = bool(checks.get("check_teoria", False))
        payload["check_resumo"] = bool(checks.get("check_resumo", False))
        payload["check_questao"] = bool(checks.get("check_questao", False))
        payload["check_revisao"] = bool(checks.get("check_revisao", False))

    try:
        # tenta achar linha existente
        resp = supabase.table("progress_item").select("id").eq("user_id", user_id).eq("tema_key", tk).eq("descr_idx", descr_idx).limit(1).execute()
        rows = getattr(resp, "data", None) or resp.data or []
        if rows:
            # update
            supabase.table("progress_item").update(payload).eq("user_id", user_id).eq("tema_key", tk).eq("descr_idx", descr_idx).execute()
            st.info("upsert_progress_item: atualizou progress_item")
        else:
            # insert
            supabase.table("progress_item").insert(payload).execute()
            st.info("upsert_progress_item: inseriu progress_item")
        return
    except Exception as e:
        # tenta fallback upsert
        try:
            supabase.table("progress_item").upsert(payload).execute()
            st.info("upsert_progress_item: upsert fallback executado")
            return
        except Exception as e2:
            st.error(f"upsert_progress_item: falha ao gravar progress_item: {e2}")
            raise




