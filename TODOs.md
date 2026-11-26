## 1. Theoretical & Architectural Analysis

### 1.1 Evaluating the Two Formulations Against BDI Theory

Your intuition hits directly on the core divide in both the philosophy of action (Michael Bratman) and formal multi-agent logics (Rao & Georgeff; Cohen & Levesque). The two statements you proposed actually capture **two complementary halves** of how Beliefs and Intentions relate in BDI theory — and distinguishing them clarifies exactly how Ontology should architect this layer.

#### Statement A: *"Intentions are a data structure that organizes an interface of beliefs."*

**Alignment: Very strong with Bratman's Planning Theory (1987) and operational BDI architectures (PRS, AgentSpeak/Jason, ABL).**

In Bratman's functionalist account, Intentions are not passive tags; they are **plan structures** that perform three organizational jobs over an agent's cognitive state:

1. **Relevance Framing (The "Interface"):** A Sprite holds many beliefs simultaneously (where doors lead, who is a friend, what items cost, where enemies were last seen). An active Intention node (`hunt`, `find`, `barter`, `speak`) selects *which slice of the Belief Base is actively queried* to govern the next transition or Action. In Ontology, the Intention Transition Matrix literally functions as an index mapping each Intention node to the subset of Belief predicates relevant to that plan step.
2. **Inertia & Commitment:** Intentions stabilize deliberation — an agent does not re-evaluate every Desire on every tick, only the termination/reconsideration predicates bound to its active Intention (`complete`, `lost`, `frightened`, category mismatch).
3. **Means–End Structuring:** An Intention links a Desire to an Action sequence mediated by belief preconditions (`find -> interact` once believed within `action.radius`).

*One nuance from BDI theory:* Intentions **index and query** Beliefs, but they do not **own** them. Beliefs persist independently of any single Intention (believing Door `d1` leads to Layer `1` or believing `archaxes` is dead survives transitions across `hunt`, `escape`, `idle`, and `wander`).

#### Statement B: *"Beliefs are the formal structure of Intentions."*

**Alignment: Strong in formal modal BDI logic (Rao & Georgeff's $BDI_{CTL^*}$; Cohen & Levesque 1990) — with one philosophical distinction.**

In Kripke-semantics BDI logic, an agent's mental state is defined over possible worlds via three accessibility relations: Belief ($\mathcal{B}$), Desire ($\mathcal{D}$), and Intention ($\mathcal{I}$). Under the standard **Realism / Consistency Axioms**:

$$\mathcal{I} \subseteq \mathcal{D} \subseteq \mathcal{B} \qquad \text{and} \qquad \text{Intend}_a(\phi) \implies \text{Bel}_a(\neg \phi) \land \text{Bel}_a(\diamond \phi)$$

An agent can only rationally intend futures that lie *inside the space of worlds it believes are possible* and not yet realized. In that formal sense, **Beliefs constitute the epistemic domain of discourse** over which Intentions are defined and evaluated: every transition predicate $\phi_\tau$ is formally a function of agent $a$'s belief state $B_a$, never of the objective world $W$.

*The philosophical caveat (Direction of Fit):* Beliefs alone cannot *generate* or *constitute* Intentions because they have opposite **directions of fit** (Anscombe / Searle):

| Attitude | Direction of Fit | Role in Ontology (Post-Phase 06.02) |
| --- | --- | --- |
| **Beliefs ($B_a$)** | Mind $\to$ World (aims to represent what *is*) | **Missing unified layer** — currently split between `memory` and omniscient `Board` globals (`sprites`, `assets`) |
| **Desires ($D_a$)** | World $\to$ Mind (what the agent *wants*) | `Instincts` + `psyche.motivation` + `memory.goals` (and active committed `sprite.goal` + `memory.stack`) |
| **Intentions ($I_a$)** | World $\to$ Mind, *committed* (how the agent *plans to act*) | `sprite.intention` + Intention Loops $\langle I, \pi, \beta \rangle$ in `intentions/main.yaml` |

**Synthesis for Ontology:**
> **Beliefs** form the subjective epistemic domain over which ISL predicates are evaluated; **Desires/Goals** are the teleological targets chosen over that domain; **Intentions** are the committed plan states that organize which Belief predicates trigger transitions and Actions.

---

### 1.2 Analyzing the Technical Problem: Relativizing the ISL Environment

At the **end state of Phase 06.02**, Ontology has clean modular boundaries (`Perception`, `GoalResolver`, `Recall`, `Instincts`, `TransitionMechanics`) and a strict `SpriteState(CharacterState)` hierarchy. Yet the ISL evaluation signature still couples the Sprite's mind directly to **objective World state ($W$)**:

$$\text{Phase 06.02 Evaluation:} \quad \text{locals} = \{\,\texttt{sprite}: s, \;\; \texttt{sprites}: W_{\text{characters}}, \;\; \texttt{assets}: W_{\text{layer}}\,\}$$

This leaves four structural leaks that cannot be patched solely by writing careful YAML rules:

1. **Omniscient Character State (`sprites`):** Even with `Perception.track` freezing `goal.position` when unseen, `target.complete` (`not sprites.get(...) or ...dead`) and `mock -> threaten` (`sprites.get(...).intention`) still read live global character states across walls, distances, and Layers. A Sprite instantly learns an enemy died across the map.
2. **Omniscient Layer Asset State (`assets`):** `object.complete`, `resource.complete`, and `door.lost` query `board.states(sprite.layer)`. If another NPC harvests a Resource or destroys a Door outside the Sprite's `vision.radius`, the Sprite telepathically drops the Goal without ever walking there to discover its absence.
3. **No Representation of False, Stale, or Testimonial Beliefs:** Because live `Board` dicts are the source of truth, a Sprite cannot believe something *false* (an outdated Resource location, a mistaken price, a rumor about where the Player fled, or an enemy that slipped away into stealth). Yet Ontology's entire `Narratives` / `Rumors` / `Emergence` design depends on asymmetric information propagating between agents!
4. **Private Mind-Reading Risk:** As `Motivations`, `Commerce`, and `Plots` expand (e.g., `conquest` checking a rival's property or `barter` checking inventory), passing raw `SpriteState` instances in `sprites` exposes *every NPC's private internal state* (`inventory`, `memory`, `psyche.motivation`) to every other NPC.

#### The Relativized Architecture: Mind vs. Body Boundary

The solution is to enforce epistemic relativization **by construction** — removing objective `Board` collections (`sprites`, `assets`) from ISL locals entirely:

$$\text{Phase 06.05 Evaluation:} \quad \text{locals} = \{\,\texttt{sprite}: s, \;\; \texttt{beliefs}: B_s\,\}$$

This draws a hard boundary between the **Body** (sensorimotor systems interacting with objective `Board` $W$) and the **Mind** (deliberative systems operating exclusively over subjective `Beliefs` $B_s$):

* **Objective World ($W$) $\xrightarrow{\text{Observe}}$ Percept ($O_s(t)$):** `Perception` reads `Board` within the Sprite's Layer, `vision.radius`, directional cone / line-of-sight (`geometry.los`, `geometry.cone`), extracting *only externally observable projections* (`position`, `layer`, `dead`, `action`, visible `equipment`, `switch`, `stage` — never private `inventory` or `psyche`).
* **Belief Revision ($B_s(t) = \text{Revise}(B_s(t-1), O_s(t), M_s(t))$):**
  * **Positive Revision (Direct Sighting):** Updates or inserts sparse `EntityBelief` records in place, stamping `seen_at = current_tick` and `source = DIRECT` (`confidence = 1.0`).
  * **Negative Revision (Observed Absence):** When the Sprite's sensory field covers the *believed coordinates* of a static entity (`object`, `resource`, `door`, `property`) and that entity is absent from $O_s(t)$, `Perception` revises `belief.exists = False` (or evicts it). For mobile entities (`character`), absence merely means `seen_at < current_tick` (not visible here — triggering `lost` + `confusion`, *not* falsely believing they died!).
  * **Testimonial Revision (Rumor / Speech):** `SocialMechanics` merges shared beliefs during `speak` with `source = RUMOR`, weighted by `relationships` trust and freshness (`seen_at`), where direct observation always dominates hearsay.
* **Zero-Reset Visibility & Zero-Allocation Discipline:** Storing monotonic `seen_at: int` on each `EntityBelief` and comparing `belief.seen_at == beliefs.tick` gives $O(1)$ visibility checks (`beliefs.visible(name)`) without an $O(|B_s|)$ per-tick reset loop, and mutating `@dataclass(slots=True)` belief records in place avoids inner-loop GC churn.

---

## 2. Backlog Proposal
