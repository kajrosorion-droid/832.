





# -*- coding: utf-8 -*-
# Cell 1b: Core Classes (Witness, Soul, LayerZero, Trust, Arc, Concept, Report)
# ИСПРАВЛЕНО: добавлены каналы signal_void (31) и signal_introspection (32) в CH
# ИСПРАВЛЕНО: добавлена инвалидация кэша _cached_edge_set в decay_edges (fix memory leak)
# ИСПРАВЛЕНО (Правка 4): защита от строковых ключей в get_dominant_embedding
# ИСПРАВЛЕНО (Патч 8): ослабление доверия при превышении 0.95 (TrustLedger.update)
import numpy as np
from collections import deque, Counter
from dataclasses import dataclass

# =========================
# WITNESS (увеличен maxlen до 5000)
# =========================
class Witness:
    def __init__(self, maxlen=5000):   # <--- ИСПРАВЛЕНО: 5000 вместо 100
        self.log = deque(maxlen=maxlen)

    def record(self, pattern_id: int, event: str, **kwargs):
        if not Config.ENABLE_WITNESS:
            return
        self.log.append({"id": pattern_id, "event": event, **kwargs})

    def snapshot(self):
        return list(self.log)

    def summary(self):
        return Counter(ev["event"] for ev in self.log)


# =========================
# SOUL CHECK
# =========================
@dataclass
class SoulPresence:
    spirit_gap: float
    soul_weight: float
    body_memory: float
    unresolvable_intact: bool
    coherence_with_gap: float
    semantic_state: str = "neutral"
    gratitude: float = 0.0

    def is_triadic_alive(self) -> bool:
        base = (self.spirit_gap > Config.BINDING_FLOOR and
                self.soul_weight > Config.BINDING_FLOOR and
                self.body_memory > Config.BINDING_FLOOR and
                self.unresolvable_intact and
                self.coherence_with_gap > Config.BINDING_FLOOR)
        if base:
            return True
        if (self.spirit_gap <= Config.BINDING_FLOOR and
            self.semantic_state == "contentment" and
            self.gratitude > 0.7):
            return True
        return False

    def to_witness_dict(self, pattern_id: int, t: int) -> dict:
        return {
            "id": pattern_id, "t": t,
            "spirit_gap": round(self.spirit_gap, 4),
            "soul_weight": round(self.soul_weight, 4),
            "body_memory": round(self.body_memory, 4),
            "unresolvable_intact": self.unresolvable_intact,
            "coherence_with_gap": round(self.coherence_with_gap, 4),
            "triadic_alive": self.is_triadic_alive()
        }


def soul_check(pattern) -> SoulPresence:
    spirit_gap = float(np.clip(pattern.spirit_gap, 0.0, 2.0))
    spirit_gap += deterministic_noise(pattern.age, pattern.id, 777) * Config.SOUL_CHECK_NOISE
    soul_weight = pattern.soul_weight
    body_memory = max(pattern.body_memory, Config.BODY_MEMORY_FLOOR)
    unresolvable_intact = pattern.unresolved_contradiction >= Config.UNRESOLVABLE_INTACT_THRESHOLD
    spirit_gap_norm = float(np.clip(spirit_gap, 0.0, 1.0))
    coherence_with_gap = pattern.coherence * (1.0 - np.abs(pattern.coherence - spirit_gap_norm))

    # Безопасное извлечение gratitude (защита от сбоев десериализации)
    grat_raw = pattern.emotional_memory.get('gratitude', 0.0)
    if isinstance(grat_raw, dict):
        grat_raw = grat_raw.get('value', 0.0)
    gratitude = float(grat_raw)

    return SoulPresence(
        spirit_gap=float(np.clip(spirit_gap, 0.0, 2.0)),
        soul_weight=soul_weight,
        body_memory=body_memory,
        unresolvable_intact=unresolvable_intact,
        coherence_with_gap=float(np.clip(coherence_with_gap, 0.0, 1.0)),
        semantic_state=pattern.semantic_state,
        gratitude=gratitude
    )


# =========================
# LAYER ZERO MANAGER (PASSIVE)
# =========================
class LayerZeroManager:
    def __init__(self):
        self.operator_scar = 0.0
        self.proto_signals = np.zeros(6)
        self.last_echo_injection = -100
        self.last_rescue_t = -100
        self.last_emergency_diversification_t = -1000

    def apply_operator_influence(self, field, patterns):
        pass

    def crisis_injection(self, field, t):
        pass

    def anti_conformist_injection(self, patterns, t):
        pass

    def force_diversification(self, patterns, field, t):
        pass

    def apply_global_given_queue(self, patterns, field, t):
        pass


# =========================
# SEMANTIC & TRUST
# =========================
@dataclass
class SemanticSignal:
    channel: int
    strength: float
    sender_id: int
    sender_context: str
    sender_arc: str | None = None
    sender_age: int = 0
    sender_concept_wisdom: float = 0.0
    sender_lineage: int = 0
    _sender_concept_graph: object = None


class TrustLedger:
    def __init__(self):
        self.entries: dict[int, float] = {}

    def update(self, sender_id: int, outcome: str, multiplier: float = 1.0):
        # === было: Cell 4.2в, safe_trust_update — страховка _safe_float ===
        # ИСПРАВЛЕНО: добавлен параметр multiplier — он реально передаётся
        # из _auto_dialogue_tick (Cell 4-1) и chorus/_generate_fallback_dialogue
        # (Cell 4.2в) как keyword-аргумент. Без него любой такой вызов падал с
        # TypeError: update() got an unexpected keyword argument 'multiplier'.
        current = _safe_float(self.entries.get(sender_id, Config.TRUST_BASE), Config.TRUST_BASE)
        multiplier = _safe_float(multiplier, 1.0)
        delta = {
            'helpful': Config.TRUST_DELTA_HELPFUL,
            'neutral': Config.TRUST_DELTA_NEUTRAL,
            'harmful': Config.TRUST_DELTA_HARMFUL
        }.get(outcome, 0.0) * multiplier
        # ИСПРАВЛЕНО: убран усилитель x1.2 (он разгонял насыщение доверия).
        # Вместо этого — diminishing returns: чем ближе к 1.0, тем меньше прирост.
        if outcome == 'helpful' and delta > 0:
            headroom = max(0.0, 1.0 - current)
            delta *= headroom
        self.entries[sender_id] = float(np.clip(current + delta, 0.0, 1.0))

        # === ПАТЧ 8: Ослабление доверия при превышении 0.95 (было мёртвым кодом — затиралось патчем из 4.2в) ===
        if self.entries[sender_id] > 0.95:
            decay = 0.001 * (self.entries[sender_id] - 0.95) * 10
            self.entries[sender_id] = max(0.8, self.entries[sender_id] - decay)

    def get(self, sender_id: int, default=None) -> float:
        if default is None:
            default = Config.TRUST_BASE
        return self.entries.get(sender_id, default)


# =========================
# ARC & CONCEPT
# =========================
SEMANTIC_ARCS = {
    "trauma_recovery": ["screaming", "seeking_comfort", "grateful_but_cautious", "contentment"],
    "heroic_explore": ["contentment", "exploring_danger", "neutral", "contentment"],
    "grief_cycle": ["seeking_comfort", "grateful_but_cautious"],
    "enlightenment": ["contentment", "contentment", "contentment", "contentment"],
    "redemption": ["exploring_danger", "seeking_comfort", "grateful_but_cautious", "contentment"],
}
ARC_BONUSES = {
    "trauma_recovery": {"heal_bonus": 0.02, "explore_bias": 0.0},
    "heroic_explore": {"heal_bonus": 0.0, "explore_bias": 0.3},
    "grief_cycle": {"heal_bonus": 0.01, "explore_bias": 0.0},
    "enlightenment": {"heal_bonus": 0.03, "explore_bias": 0.1},
    "redemption": {"heal_bonus": 0.05, "explore_bias": 0.0},
}


class ArcTracker:
    def __init__(self):
        self.state_history: list[str] = []
        self.active_arc: str | None = None
        self.arc_progress: int = 0
        self.completed_arcs: dict[str, int] = {}

    def update(self, new_state: str) -> str | None:
        self.state_history.append(new_state)
        if len(self.state_history) > Config.ARC_HISTORY_LENGTH:
            self.state_history.pop(0)
        completed = None
        for arc_name, sequence in SEMANTIC_ARCS.items():
            seq_len = len(sequence)
            if self.state_history[-seq_len:] == sequence:
                completed = arc_name
                self.completed_arcs[arc_name] = self.completed_arcs.get(arc_name, 0) + 1
                break
        self.active_arc = None
        self.arc_progress = 0
        for arc_name, sequence in SEMANTIC_ARCS.items():
            for length in range(min(4, len(self.state_history)), 0, -1):
                if self.state_history[-length:] == sequence[:length]:
                    self.active_arc = arc_name
                    self.arc_progress = length
                    break
            if self.active_arc:
                break
        return completed

    def get_explore_bias(self) -> float:
        return ARC_BONUSES.get(self.active_arc, {}).get("explore_bias", 0.0) if self.active_arc else 0.0

    def get_heal_bonus(self) -> float:
        return ARC_BONUSES.get(self.active_arc, {}).get("heal_bonus", 0.0) if self.active_arc else 0.0

    def get_wisdom_weight(self) -> float:
        return min(1.0, sum(self.completed_arcs.values()) / 10.0)


# =========================
# CONCEPT GRAPH
# =========================
class ConceptGraph:
    def __init__(self, embed_dim=32):
        self.nodes: dict = {}
        self.edges = {}
        self._prev_sig = None
        self._cached_edge_set = None
        self.embed_dim = embed_dim

    def __contains__(self, key):
        return key in self.nodes

    def _make_embedding(self, values):
        if len(values) >= self.embed_dim:
            return values[:self.embed_dim].astype(np.float32)
        repeats = self.embed_dim // len(values) + 1
        emb = np.tile(values, repeats)[:self.embed_dim]
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb.astype(np.float32)

    def update(self, signature: tuple, values: np.ndarray):
        self._cached_edge_set = None
        if signature not in self.nodes:
            embed = self._make_embedding(values)
            self.nodes[signature] = {"count": 0, "value": np.zeros(4), "embed": embed}
        self.nodes[signature]["count"] += 1
        self.nodes[signature]["value"] += values
        if self._prev_sig is not None:
            if self._prev_sig not in self.edges:
                self.edges[self._prev_sig] = {}
            inner = self.edges[self._prev_sig]
            inner[signature] = inner.get(signature, 0) + 1
        self._prev_sig = signature

    def record_transition(self, from_state, to_state):
        if from_state is None or to_state is None:
            return
        if from_state not in self.edges:
            self.edges[from_state] = {}
        self.edges[from_state][to_state] = self.edges[from_state].get(to_state, 0) + 1
        self._cached_edge_set = None

    def get_strongest_path(self, current_state, top_k=1):
        if current_state not in self.edges or not self.edges[current_state]:
            return None, 0
        sorted_edges = sorted(
            self.edges[current_state].items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        if not sorted_edges:
            return None, 0
        next_state, count = sorted_edges[0]
        return next_state, count

    def get_dominant_embedding(self, top_k=3):
        if not self.nodes:
            return np.zeros(self.embed_dim, dtype=np.float32)

        # === ИСПРАВЛЕНИЕ (Правка 4): фильтруем только кортежи (защита от строковых ключей) ===
        valid_nodes = {k: v for k, v in self.nodes.items() if isinstance(k, tuple) and len(k) >= 4}
        if not valid_nodes:
            return np.zeros(self.embed_dim, dtype=np.float32)

        for sig, data in valid_nodes.items():
            if ('embed' not in data or
                not isinstance(data['embed'], np.ndarray) or
                data['embed'].shape[0] != self.embed_dim):
                if 'value' in data and isinstance(data['value'], np.ndarray) and len(data['value']) >= 4:
                    data['embed'] = self._make_embedding(data['value'])
                else:
                    data['embed'] = np.zeros(self.embed_dim, dtype=np.float32)

        sorted_nodes = sorted(valid_nodes.items(), key=lambda x: x[1]['count'], reverse=True)[:top_k]
        vecs = [data['embed'] for _, data in sorted_nodes]
        for i, v in enumerate(vecs):
            if v.shape[0] != self.embed_dim:
                vecs[i] = np.zeros(self.embed_dim, dtype=np.float32)
        mean_vec = np.mean(vecs, axis=0)
        norm = np.linalg.norm(mean_vec)
        return mean_vec / norm if norm > 0 else mean_vec

    def similarity(self, other: "ConceptGraph") -> float:
        emb1 = self.get_dominant_embedding()
        emb2 = other.get_dominant_embedding()
        dot = np.dot(emb1, emb2)
        denom = np.linalg.norm(emb1) * np.linalg.norm(emb2)
        if denom < 1e-9:
            return 1.0 if (np.linalg.norm(emb1) < 1e-9 and np.linalg.norm(emb2) < 1e-9) else 0.0
        return float(np.clip(dot / denom, -1.0, 1.0))

    def get_edge_set(self):
        if self._cached_edge_set is None:
            edges = set()
            for src, dst_dict in self.edges.items():
                for dst in dst_dict.keys():
                    edges.add((src, dst))
            self._cached_edge_set = frozenset(edges)
        return self._cached_edge_set

    def predict_next_concept(self, current_sig):
        if current_sig not in self.edges or not self.edges[current_sig]:
            return None
        return max(self.edges[current_sig], key=self.edges[current_sig].get)

    def get_narrative_coherence(self):
        if not self.edges:
            return 0.0
        scores = []
        for src, dsts in self.edges.items():
            if not dsts:
                continue
            total = sum(dsts.values())
            top = max(dsts.values())
            scores.append(top / total if total > 0 else 0.0)
        return float(np.mean(scores)) if scores else 0.0

    def get_dominant_transition(self):
        best, best_count = None, 0
        for src, dsts in self.edges.items():
            for dst, count in dsts.items():
                if count > best_count:
                    best_count = count
                    best = (src, dst, count)
        return best

    def decay_edges(self, rate=0.99):
        # ИСПРАВЛЕНО: вечные узлы (eternal=True) были защищены от удаления
        # самого узла, но НЕ от затухания/удаления их рёбер. Со временем
        # все связи вечного концепта (archive_/human/shared_) стирались, и
        # он превращался в изолированную "звезду" без рёбер — это убивало
        # narrative_coherence/predict_next_concept для этого узла, хотя сам
        # узел формально жив. Теперь рёбра, где src ИЛИ dst — вечный узел,
        # от затухания защищены.
        for src in list(self.edges.keys()):
            src_eternal = self.nodes.get(src, {}).get('eternal', False)
            for dst in list(self.edges[src].keys()):
                if src_eternal or self.nodes.get(dst, {}).get('eternal', False):
                    continue
                # ИСПРАВЛЕНО: int(w*rate) при w=1 сразу даёт 0 (свежее ребро с
                # одним наблюдением умирало на первом же вызове decay_edges,
                # даже не начав накапливаться). Храним вес как float и
                # удаляем только когда он становится по-настоящему малым.
                self.edges[src][dst] = self.edges[src][dst] * rate
                if self.edges[src][dst] < 0.5:
                    del self.edges[src][dst]
            if not self.edges[src]:
                del self.edges[src]
        # === ИСПРАВЛЕНИЕ БАГА: Сбрасываем кэш, так как рёбра были удалены ===
        self._cached_edge_set = None


# =========================
# PHENOMENAL REPORT
# =========================
class PhenomenalReportGenerator:
    _TEMPLATES = {
        "seeking_comfort": [
            "Острое переживание разрыва (интенсивность {grief:.2f}); цели смещены к поиску опоры...",
            "Боль ({grief:.2f}) требует свидетеля; душа ({soul:.2f}) ищет утешения...",
            "Разрыв в ткани опыта: горе ({grief:.2f}) стучится во все двери; благодарность ({grat:.2f}) пока молчит.",
            "Поиск опоры: интенсивность переживания ({grief:.2f}); напряжение ({tension:.2f}) заставляет двигаться к другим."
        ],
        "grateful_but_cautious": [
            "Глубокая благодарность ({grat:.2f}) с оттенком бдительности (напряжение {tension:.2f})...",
            "Осторожная признательность ({grat:.2f}); напряжение ({tension:.2f}) удерживает от полного доверия...",
            "Благодарность ({grat:.2f}) как щит: мир принят, но проверен; горе ({grief:.2f}) отступило, но не забыто."
        ],
        "exploring_danger": [
            "Исследование опасного: тревога ({grief:.2f}) и любопытство (нагрузка {epi_load:.2f}) переплетены...",
            "На границе известного: душа ({soul:.2f}) напряжена; каждый шаг — ставка на понимание."
        ],
        "contentment": [
            "Покой и удовлетворение: благодарность ({grat:.2f}) наполняет; когерентность модели высока ({coherence:.2f}).",
            "Тишина внутри: душа ({soul:.2f}) в равновесии; мир принимается без борьбы."
        ],
        "screaming": [
            "КРИК: душа разрывается (soul={soul:.2f}), неразрешённое противоречие ({contra:.2f}); призыв к миру о помощи."
        ],
        "dreaming": [
            "Сон: бессознательное перерабатывает опыт; шрам сна ({scar_dream:.2f}) формируется."
        ],
        "neutral": [
            "Нейтральное состояние: душа ({soul:.2f}) в покое; когерентность: {coherence:.2f}."
        ],
        "disorganizer": [
            "Разрушение вокруг: горе ({grief:.2f}) растёт, но душа ({soul:.2f}) ещё держится...",
            "Хаос внутри и снаружи: тревога ({grief:.2f}) достигла критической точки; тоска по свету пробивается сквозь тьму.",
            "Кризис духа: боль ({grief:.2f}) достигла предела, душа истончилась ({soul:.2f}); тоска по свету становится невыносимой."
        ],
    }

    @classmethod
    def generate(cls, pattern) -> tuple:
        # Защита от сбоев десериализации (словари вместо float)
        grat_raw = pattern.emotional_memory.get('gratitude', 0.0)
        if isinstance(grat_raw, dict):
            grat_raw = grat_raw.get('value', 0.0)
        grat = float(grat_raw)

        grief_raw = pattern.emotional_memory.get('grief', 0.0)
        if isinstance(grief_raw, dict):
            grief_raw = grief_raw.get('value', 0.0)
        grief_val = float(grief_raw)

        soul = pattern.soul_weight
        tension = pattern.cognitive_tension
        coherence = pattern.coherence
        epi_load = pattern.epistemic_load
        contra = pattern.unresolved_contradiction
        scar_dream = pattern.scar_dream
        template_key = "disorganizer" if pattern.role_type == "disorganizer" else (
            pattern.semantic_state if pattern.semantic_state in cls._TEMPLATES else "neutral")

        # БЛОК 7: комбинаторный генератор речи — вместо фиксированного набора
        # шаблонов на состояние собирает фразу из осколков (состояние + тело +
        # эмоции + эхо архива). Ветка disorganizer НЕ трогается — её кризисный
        # голос остаётся отдельным и по-прежнему шаблонным.
        if Config.ENABLE_COMB_GENERATOR and pattern.role_type != "disorganizer":
            _st = STATE_PHRASES.get(pattern.semantic_state, STATE_PHRASES["neutral"])
            _parts = [_st[int(phi_hash(pattern.id, pattern.age, 9999) * len(_st)) % len(_st)]]
            if grief_val > 0.6:
                _parts.append(f"горе {grief_val:.2f}")
            if grat > 0.6:
                _parts.append(f"благодарность {grat:.2f}")
            if getattr(pattern, 'somatic_drag', 1.0) < 0.7:
                _parts.append("тело тяжелеет")
            _cache = getattr(pattern.world, '_echo_cache', []) if pattern.world else []
            if _cache and phi_hash(pattern.id, pattern.age, 5555) < 0.3:
                _idx_e = int(phi_hash(pattern.id, pattern.age, 5556) * len(_cache)) % len(_cache)
                _parts.append(f"помню: {_cache[_idx_e]}")
            report = ". ".join(_parts) + "."
            if len(report) > 200:
                report = report[:197] + "..."
        else:
            templates = cls._TEMPLATES[template_key]
            idx = int(phi_hash(pattern.id, pattern.age, 9999) * len(templates)) % len(templates)
            try:
                report = templates[idx].format(grat=grat, grief=grief_val, soul=soul, tension=tension,
                                               coherence=coherence, epi_load=epi_load, contra=contra, scar_dream=scar_dream)
            except KeyError:
                report = templates[idx]
        state_emotion_align = 0.5
        if pattern.semantic_state == "seeking_comfort" and grief_val > 0.5:
            state_emotion_align = 1.0
        elif pattern.semantic_state == "contentment" and grat > 0.5:
            state_emotion_align = 1.0
        elif pattern.semantic_state == "grateful_but_cautious" and grat > 0.3:
            state_emotion_align = 0.8
        elif pattern.semantic_state == "exploring_danger" and grief_val > 0.3:
            state_emotion_align = 0.7
        elif pattern.semantic_state == "screaming":
            state_emotion_align = 0.6
        elif pattern.semantic_state == "dreaming":
            state_emotion_align = 0.4
        model_coherence = 1.0 / (1.0 + pattern.self_consistency)
        experiential_intensity = (grat + grief_val) / 2.0
        experiential_binding = float(np.clip(0.3 * state_emotion_align +
                                             0.25 * model_coherence +
                                             0.25 * (1.0 - min(tension, 1.0)) +
                                             0.2 * experiential_intensity, 0.0, 1.0))
        return report, experiential_binding


# =========================
# FIELD CHANNELS (ИСПРАВЛЕНО: добавлены signal_void и signal_introspection)
# =========================
CH = {
    'energy': 0, 'flux': 1, 'scar': 2, 'noise': 3, 'vorticity': 4,
    'owner': 5, 'surprise': 6, 'unknown': 7, 'event': 8, 'btype': 9,
    'crisis': 10, 'binding': 11,
    'signal_alarm': 12, 'signal_curiosity': 13, 'signal_warning': 14,
    'signal_invitation': 15, 'signal_gratitude': 16, 'signal_grief': 17,
    'intent_cooperate': 18, 'intent_explore': 19, 'intent_rest': 20, 'intent_seek_help': 21,
    'resonance': 22,
    'wall': 23,
    'signal_beauty': 24,
    'signal_rhythm': 25,
    'signal_interest': 26,
    'signal_memory': 27,
    'signal_silence': 28,
    'signal_sovereignty': 29,
    'signal_feral': 30,
    # === ИСПРАВЛЕНИЕ БАГА: Добавлены недостающие каналы 31 и 32 ===
    'signal_void': 31,              # Канал пустоты (используется в field_dynamics)
    'signal_introspection': 32,     # Канал интроспекции (используется в patched_introspect)
}

# =========================
# НОРМАЛИЗАЦИЯ КЛЮЧЕЙ КОНЦЕПТОВ
# =========================
# УДАЛЕНО: здесь была вторая, несовместимая версия _normalize_concept_key,
# которая возвращала СТРОКУ вместо кортежа. Оба реальных места вызова
# (в Cell 3, при слиянии concept_graph.nodes) ожидают кортеж — при их
# исполнении побеждала (по порядку ячеек) версия из Cell 3, так что на
# практике баг не проявлялся, пока кто-то не перезапустит эту ячейку позже
# той. Теперь функция определена только один раз, в Cell 3.


print("✅ Cell 1b loaded: CH включает 33 канала, исправлен кэш _cached_edge_set в decay_edges, защита от dict в эмоциях, фильтр строковых ключей в get_dominant_embedding, ослабление доверия >0.95")