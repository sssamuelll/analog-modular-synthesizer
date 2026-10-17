//! Motor de eventos del transporte por tic (papel v3) sobre la maquina REAL de `core`.
//! Una CPU con prioridades de NVIC (menor numero = mas urgente), secciones PRIMASK (pasos
//! atomicos), seis ranuras con `Transporte`, `Triple`, `Anillo<8>`, `Subida` y la politica
//! `maestro_j2::Ranura` sin tocar. El hardware (SPI, GPDMA, TIM7, IWDG) es un modelo con
//! las cifras medidas de EN-PLACA.md; lo ESTIMADO se dice donde se usa.

use crate::buzones_j2::{codigo, Anillo, Lectura as LecSubida, Subida, Triple};
use crate::maestro_j2::{plazo_us, Accion, Evento, Ranura as Politica, Tsize, Umbrales};
use crate::transporte_j2::{
    tics_de_plazo, tics_fusionados, Aviso, Entrada, Estado, Lectura, Reloj64, Salida, Transporte,
};
use std::cmp::Reverse;
use std::collections::{BinaryHeap, VecDeque};

pub const N: usize = 6;
pub const PERIODO_NS: u64 = 125_000;

/// ciclos de CPU a 800 MHz -> ns
pub fn cy(c: u64) -> u64 {
    (c as f64 * 1.25).round() as u64
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Budget {
    Ninguno,
    /// la propuesta de v3 §2.5: `max` escaladas por `ventana_tics`; `init_cero` = las estampas
    /// arrancan en 0 en vez de vacias (la lectura literal de «guarda los tics de las ultimas 3»).
    V3 { max: usize, ventana_tics: u32, init_cero: bool },
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Deny {
    /// la recuperacion no publica `HECHA` y deja `EN_CURSO`: la muerte la da la cota `Reiniciando`.
    Retener,
    /// la recuperacion marca `Muerta` bajo PRIMASK (un segundo escritor del estado).
    Directo,
}

#[derive(Clone)]
pub struct Cfg {
    pub f_sck: u64,
    pub eps_ns: u64,
    pub msg: [u16; N],
    pub active: [bool; N],
    pub cold: bool,
    pub budget: Budget,
    pub deny: Deny,
    pub t_canal_ns: u64,
    pub cotas: (u8, u8),
    pub feed_period_ns: u64,
    pub iwdg_ns: u64,
    pub susp_ns: u64,
    pub pat: Option<fn(usize, u64) -> u16>,
    pub gap_ns: u64,
    pub plan_extra_ns: u64,
}

impl Cfg {
    pub fn base() -> Cfg {
        Cfg {
            f_sck: 6_250_000,
            eps_ns: 1_500, // ESTIMADO: arranque del SPI + latencia de DMA; nadie lo ha medido
            msg: [25; N],
            active: [true; N],
            cold: false,
            budget: Budget::Ninguno,
            deny: Deny::Retener,
            t_canal_ns: 25_000,
            cotas: (100, 100),
            feed_period_ns: 5_000_000, // ESTIMADO: el supervisor (#291) no existe
            iwdg_ns: 60_000_000,       // ESTIMADO: «estrictamente mayor que ~50 ms»
            susp_ns: 600,
            pat: None,
            gap_ns: 2_000,
            plan_extra_ns: 0,
        }
    }
}

#[derive(Default, Clone)]
pub struct HwSlot {
    pub in_flight: bool,
    pub frame_end: Option<u64>,
    pub hung: bool,
    pub gen: u64,
    pub chan_stuck: bool,
    pub bad: bool,
    pub poison_next: bool,
    pub stuck_next: Option<bool>,
    pub suspf_at: Option<u64>,
    pub cstart: u64,
}

pub struct SlotW {
    pub on: bool,
    pub tic: Transporte,
    pub rx_actual: u8,
    pub largo: u16,
    pub hw: HwSlot,
    pub pol: Politica,
    pub buzon: Triple,
    pub meta: [(u8, u16); 3],
    pub anillo: Anillo<8>,
    pub ring_occ: usize,
    pub ring_max: usize,
    pub ring_lost: u32,
    pub subida: Subida,
    pub largo_subida: u16,
    pub rec_pedida: bool,
    pub rec_en_curso: bool,
    pub rec_hecha: bool,
    pub rec_t_hecha: u64,
    pub denied: bool,
    pub sucia: bool,
    pub sellos: u64,
    pub sin_bajada: u32,
    pub errores_dma: u32,
    pub muertas: u32,
    pub recuperaciones: u32,
    pub giros: u32,
    pub plazos: u32,
    pub colateral: u32,
    pub composes: u64,
    pub last_valid: u64,
    pub max_gap: u64,
    pub inicio_susp: u64,
    pub scratch: Option<(Estado, Salida)>,
}

#[derive(Clone, Copy, Debug)]
pub enum Fx {
    None,
    TicEntry,
    TicRead(usize),
    TicClose(usize),
    TicArm(usize),
    TicPost(usize),
    TicEnd,
    PlanEntry,
    PlanDrain(usize),
    PlanCompose(usize),
    PlanEnd,
    RecEntry,
    RecScan(usize),
    RecStart(usize),
    RecSusp(usize),
    RecPoll(usize),
    RecResetCh(usize),
    RecDecide(usize),
    EscPrep(usize),
    EscCrit(usize),
    EscProg(usize, usize),
    EscEnd(usize),
    SpiReset(usize),
    RecProg(usize),
    RecDone(usize),
    DenyKill(usize),
    Feeder,
    P2End,
}

#[derive(Clone, Copy, Debug)]
pub struct Step {
    pub ns: u64,
    pub atomic: bool,
    pub fx: Fx,
}

pub struct Job {
    pub prio: u8,
    pub name: &'static str,
    pub steps: VecDeque<Step>,
    pub rem: u64,
    pub started: bool,
}

impl Job {
    fn new(prio: u8, name: &'static str) -> Job {
        Job { prio, name, steps: VecDeque::new(), rem: 0, started: false }
    }
    fn push_back(&mut self, ns: u64, atomic: bool, fx: Fx) {
        self.steps.push_back(Step { ns, atomic, fx });
    }
    fn push_front(&mut self, ns: u64, atomic: bool, fx: Fx) {
        self.steps.push_front(Step { ns, atomic, fx });
        self.started = false;
    }
}

#[derive(Clone, Copy, Debug)]
pub enum HwEv {
    Uev,
    P2 { dur: u64, atomic: bool },
    P2Seq { id: usize },
    Inject { slot: usize, kind: Inj },
    StallStart { until: u64 },
    FrameDone { slot: usize, gen: u64 },
    FeedTimer,
    IwdgExpire { deadline: u64 },
    Stop,
}

#[derive(Clone, Copy, Debug)]
pub enum Inj {
    /// SPI envenenado: la proxima armada no acaba; el canal para bien; lo cura el reset del SPI
    Hang,
    /// canal GPDMA atascado: no llega a SUSPF; lo cura el reset del GPDMA1 (`persistente` = no lo cura)
    Stuck { persistente: bool },
}

#[derive(Clone, Debug)]
pub struct Mark {
    pub t: u64,
    pub slot: i32,
    pub what: &'static str,
    pub x: i64,
}

pub struct Sim {
    pub cfg: Cfg,
    pub now: u64,
    pub running: Option<Job>,
    pub stack: Vec<Job>,
    pub pend_tic: bool,
    pub pend_plan: bool,
    pub pend_rec: bool,
    pub pend_feed: bool,
    pub pend_p2: VecDeque<Vec<(u64, bool)>>,
    heap: BinaryHeap<Reverse<(u64, u64)>>,
    evs: Vec<Option<HwEv>>,
    pub tics: u32,
    pub last_uev: u64,
    ultima_entrada: u32,
    pub tic_t0: u64,
    pub tics_fus: u32,
    pub tics_tard: u32,
    pub retraso_max_us: u32,
    pub uev_merged: u32,
    pub reloj: Reloj64,
    pub plan_now_us: u64,
    pub stamps: Vec<u32>,
    pub escaladas: u32,
    pub denegadas: u32,
    pub esc_times: Vec<u64>,
    pub last_seen: [u64; N],
    pub fed_at: u64,
    pub deadline: u64,
    pub iwdg_reset_at: Option<u64>,
    pub first_refusal: Option<u64>,
    pub stall_until: u64,
    pub s: Vec<SlotW>,
    pub marks: Vec<Mark>,
    pub busy: [u64; 6],
    pub stop: bool,
    pub preempt_count: u64,
    pub max_concurrent_esc: u32,
    pub in_esc: u32,
    /// (ranura, golpes en ns): al emitir el tic el primer `PlazoVencido` de esa ranura, hace pendientes
    /// estos golpes de P2 (como `acapara::si_toca_en_vencida` del banco).
    pub hold_on_vencida: Option<(usize, Vec<Vec<(u64, bool)>>)>,
    pub p2seqs: Vec<Vec<(u64, bool)>>,
    pub hold_on_escalada: Option<Vec<Vec<(u64, bool)>>>,
    pub plan_since: Option<u64>,
    pub rec_since: Option<u64>,
    pub plan_lat_max: u64,
    pub rec_lat_max: u64,
    pub trace_arm: Option<usize>,
    pub ring_hist_max: usize,
}

impl Sim {
    pub fn new(cfg: Cfg) -> Sim {
        let mut s = Vec::new();
        for n in 0..N {
            let mut pol = Politica::nueva(Umbrales::POR_DEFECTO);
            if cfg.active[n] {
                let _ = pol.paso(Evento::Identidad(true), 0);
            }
            s.push(SlotW {
                on: cfg.active[n],
                tic: Transporte::con_cotas(cfg.cotas.0, cfg.cotas.1),
                rx_actual: 0,
                largo: 0,
                hw: HwSlot::default(),
                pol,
                buzon: Triple::nuevo(),
                meta: [(1, 0); 3],
                anillo: Anillo::<8>::nuevo(),
                ring_occ: 0,
                ring_max: 0,
                ring_lost: 0,
                subida: Subida::nueva(),
                largo_subida: 0,
                rec_pedida: false,
                rec_en_curso: false,
                rec_hecha: false,
                rec_t_hecha: 0,
                denied: false,
                sucia: false,
                sellos: 0,
                sin_bajada: 0,
                errores_dma: 0,
                muertas: 0,
                recuperaciones: 0,
                giros: 0,
                plazos: 0,
                colateral: 0,
                composes: 0,
                last_valid: 0,
                max_gap: 0,
                inicio_susp: 0,
                scratch: None,
            });
        }
        let stamps = match cfg.budget {
            Budget::V3 { max, init_cero: true, .. } => vec![0u32; max],
            _ => Vec::new(),
        };
        let mut sim = Sim {
            cfg,
            now: 0,
            running: None,
            stack: Vec::new(),
            pend_tic: false,
            pend_plan: false,
            pend_rec: false,
            pend_feed: false,
            pend_p2: VecDeque::new(),
            heap: BinaryHeap::new(),
            evs: Vec::new(),
            tics: 0,
            last_uev: 0,
            ultima_entrada: 0,
            tic_t0: 0,
            tics_fus: 0,
            tics_tard: 0,
            retraso_max_us: 0,
            uev_merged: 0,
            reloj: Reloj64::nuevo(),
            plan_now_us: 0,
            stamps,
            escaladas: 0,
            denegadas: 0,
            esc_times: Vec::new(),
            last_seen: [0; N],
            fed_at: 0,
            deadline: 0,
            iwdg_reset_at: None,
            first_refusal: None,
            stall_until: 0,
            s,
            marks: Vec::new(),
            busy: [0; 6],
            stop: false,
            preempt_count: 0,
            max_concurrent_esc: 0,
            in_esc: 0,
            hold_on_vencida: None,
            p2seqs: Vec::new(),
            hold_on_escalada: None,
            plan_since: None,
            rec_since: None,
            plan_lat_max: 0,
            rec_lat_max: 0,
            trace_arm: None,
            ring_hist_max: 0,
        };
        // `lanzar`: la primera trama ya esta en el buzon cuando llega el primer tic.
        for n in 0..N {
            if sim.s[n].on {
                sim.plan_compose(n);
            }
        }
        sim.hw_at(PERIODO_NS, HwEv::Uev);
        let fp = sim.cfg.feed_period_ns;
        sim.hw_at(fp, HwEv::FeedTimer);
        sim.deadline = sim.cfg.iwdg_ns;
        let d = sim.deadline;
        sim.hw_at(d, HwEv::IwdgExpire { deadline: d });
        sim
    }

    pub fn hw_at(&mut self, t: u64, ev: HwEv) {
        let id = self.evs.len() as u64;
        self.evs.push(Some(ev));
        self.heap.push(Reverse((t, id)));
    }

    pub fn mark(&mut self, slot: i32, what: &'static str, x: i64) {
        self.marks.push(Mark { t: self.now, slot, what, x });
    }

    // ------------------------------------------------------------------------------
    // Hardware
    // ------------------------------------------------------------------------------

    fn bytes_for(&self, n: usize, k: u64) -> u16 {
        match self.cfg.pat {
            Some(f) => f(n, k),
            None => self.cfg.msg[n],
        }
    }

    pub fn frame_ns(&self, bytes: u16) -> u64 {
        bytes as u64 * 8 * 1_000_000_000 / self.cfg.f_sck + self.cfg.eps_ns
    }

    pub fn plazo_tics(&self, bytes: u16) -> u8 {
        let t = Tsize::nuevo(bytes).unwrap();
        tics_de_plazo(plazo_us(t, self.cfg.f_sck as u32, &Umbrales::POR_DEFECTO), 125)
    }

    fn lee(&self, n: usize) -> Lectura {
        let h = &self.s[n].hw;
        let done = !h.hung && h.frame_end.map_or(false, |e| self.now >= e);
        Lectura { eot: done, tcf_rx: done, tcf_tx: done, error_dma: false }
    }

    fn hw_cierra(&mut self, n: usize) {
        let h = &mut self.s[n].hw;
        h.in_flight = false;
        h.frame_end = None;
        h.hung = false;
        h.gen += 1;
    }

    fn hw_arma(&mut self, n: usize, bytes: u16) {
        let now = self.now;
        let stall = now < self.stall_until;
        let dur = self.frame_ns(bytes);
        let h = &mut self.s[n].hw;
        h.gen += 1;
        h.in_flight = true;
        h.cstart = now;
        let poisoned = std::mem::take(&mut h.poison_next);
        let stuck = h.stuck_next.take();
        if let Some(p) = stuck {
            h.chan_stuck = true;
            if p {
                h.bad = true;
            }
        }
        if h.bad {
            h.chan_stuck = true;
        }
        let hang = poisoned || stuck.is_some() || h.bad || stall;
        if hang {
            h.hung = true;
            h.frame_end = None;
        } else {
            h.hung = false;
            h.frame_end = Some(now + dur);
            let gen = h.gen;
            self.hw_at(now + dur, HwEv::FrameDone { slot: n, gen });
        }
        if poisoned || stuck.is_some() {
            self.mark(n as i32, "cstart_veneno", 0);
        }
    }

    fn hw_spi_reset(&mut self, n: usize) {
        let h = &mut self.s[n].hw;
        h.in_flight = false;
        h.frame_end = None;
        h.hung = false;
        h.gen += 1;
    }

    fn hw_gpdma_reset(&mut self) {
        for n in 0..N {
            let h = &mut self.s[n].hw;
            if h.in_flight {
                h.gen += 1;
                h.frame_end = None;
                h.hung = true;
            }
            if !h.bad {
                h.chan_stuck = false;
            }
        }
    }

    fn chan_stuck_now(&self, n: usize) -> bool {
        let h = &self.s[n].hw;
        (h.chan_stuck || self.now < self.stall_until) && (h.in_flight || h.hung)
    }

    // ------------------------------------------------------------------------------
    // Scheduler
    // ------------------------------------------------------------------------------

    fn best_pending(&self) -> Option<(u8, u8)> {
        // (prio, kind) kind: 0 tic, 1 p2, 2 plan, 3 rec, 4 feed
        let mut best: Option<(u8, u8)> = None;
        let mut consider = |p: u8, k: u8| {
            if best.map_or(true, |(bp, _)| p < bp) {
                best = Some((p, k));
            }
        };
        if self.pend_tic {
            consider(1, 0);
        }
        if !self.pend_p2.is_empty() {
            consider(2, 1);
        }
        if self.pend_plan {
            consider(3, 2);
        }
        if self.pend_rec {
            consider(4, 3);
        }
        if self.pend_feed {
            consider(5, 4);
        }
        best
    }

    fn start_pending(&mut self, kind: u8) -> Job {
        match kind {
            0 => {
                self.pend_tic = false;
                let mut j = Job::new(1, "tic");
                j.push_back(cy(125), false, Fx::TicEntry);
                j
            }
            1 => {
                let seq = self.pend_p2.pop_front().unwrap();
                let mut j = Job::new(2, "p2");
                for (dur, atomic) in seq {
                    j.push_back(dur, atomic, Fx::P2End);
                }
                j
            }
            2 => {
                if let Some(t) = self.plan_since.take() {
                    self.plan_lat_max = self.plan_lat_max.max(self.now - t);
                }
                self.pend_plan = false;
                let mut j = Job::new(3, "plan");
                j.push_back(cy(100), false, Fx::PlanEntry);
                j
            }
            3 => {
                if let Some(t) = self.rec_since.take() {
                    self.rec_lat_max = self.rec_lat_max.max(self.now - t);
                }
                self.pend_rec = false;
                let mut j = Job::new(4, "rec");
                j.push_back(cy(100), false, Fx::RecEntry);
                j
            }
            _ => {
                self.pend_feed = false;
                let mut j = Job::new(5, "feed");
                j.push_back(5_000, false, Fx::Feeder);
                j
            }
        }
    }

    fn running_atomic(&self) -> bool {
        self.running.as_ref().map_or(false, |r| r.steps.front().map_or(false, |s| s.atomic))
    }

    fn schedule(&mut self) {
        if self.pend_plan && self.plan_since.is_none() {
            self.plan_since = Some(self.now);
        }
        if self.pend_rec && self.rec_since.is_none() {
            self.rec_since = Some(self.now);
        }
        loop {
            let bp = self.best_pending();
            if self.running.is_none() {
                let top = self.stack.last().map(|j| j.prio);
                if let Some((p, k)) = bp {
                    if top.map_or(true, |tp| p < tp) {
                        let j = self.start_pending(k);
                        self.running = Some(j);
                        continue;
                    }
                }
                if let Some(j) = self.stack.pop() {
                    self.running = Some(j);
                }
                break;
            } else {
                if self.running_atomic() {
                    break;
                }
                let rp = self.running.as_ref().unwrap().prio;
                if let Some((p, k)) = bp {
                    if p < rp {
                        let r = self.running.take().unwrap();
                        self.stack.push(r);
                        self.preempt_count += 1;
                        let j = self.start_pending(k);
                        self.running = Some(j);
                        continue;
                    }
                }
                break;
            }
        }
        if let Some(r) = self.running.as_mut() {
            if !r.started {
                if let Some(s) = r.steps.front() {
                    r.rem = s.ns;
                    r.started = true;
                }
            }
        }
    }

    pub fn run_until(&mut self, t_end: u64) {
        loop {
            self.schedule();
            if self.stop {
                break;
            }
            // 1. un paso de duracion cero (o ya acabado) se completa en el acto
            let zero = self.running.as_ref().map_or(false, |r| r.started && r.rem == 0);
            if zero {
                self.complete_front();
                continue;
            }
            // 2. eventos de hardware con hora <= ahora
            if let Some(&Reverse((th, id))) = self.heap.peek() {
                if th <= self.now {
                    self.heap.pop();
                    if let Some(ev) = self.evs[id as usize].take() {
                        self.hw_event(ev);
                    }
                    continue;
                }
            }
            if self.now >= t_end {
                break;
            }
            // 3. avanzar el reloj
            let t_hw = self.heap.peek().map(|Reverse((t, _))| *t).unwrap_or(u64::MAX);
            let t_cpu = self.running.as_ref().map_or(u64::MAX, |r| self.now + r.rem);
            let t = t_hw.min(t_cpu).min(t_end);
            let dt = t - self.now;
            if let Some(r) = self.running.as_mut() {
                r.rem -= dt;
                let idx = (r.prio as usize).min(5);
                self.busy[idx] += dt;
            }
            self.now = t;
        }
    }

    fn complete_front(&mut self) {
        let mut job = self.running.take().unwrap();
        let st = job.steps.pop_front().unwrap();
        job.started = false;
        self.apply(st.fx, &mut job);
        if !job.steps.is_empty() {
            self.running = Some(job);
        }
    }

    fn hw_event(&mut self, ev: HwEv) {
        match ev {
            HwEv::Uev => {
                self.last_uev = self.now;
                if self.pend_tic {
                    self.uev_merged += 1;
                }
                self.pend_tic = true;
                self.hw_at(self.now + PERIODO_NS, HwEv::Uev);
            }
            HwEv::P2 { dur, atomic } => self.pend_p2.push_back(vec![(dur, atomic)]),
            HwEv::P2Seq { id } => {
                let q = self.p2seqs[id].clone();
                self.pend_p2.push_back(q);
            }
            HwEv::Inject { slot, kind } => match kind {
                Inj::Hang => self.s[slot].hw.poison_next = true,
                Inj::Stuck { persistente } => self.s[slot].hw.stuck_next = Some(persistente),
            },
            HwEv::StallStart { until } => {
                self.stall_until = until;
                let now = self.now;
                for n in 0..N {
                    let h = &mut self.s[n].hw;
                    if h.in_flight && !h.hung && h.frame_end.map_or(false, |e| e > now) {
                        h.hung = true;
                        h.frame_end = None;
                        h.gen += 1;
                    }
                }
                self.mark(-1, "stall_inicio", (until - now) as i64);
            }
            HwEv::FrameDone { slot, gen } => {
                let now = self.now;
                let s = &mut self.s[slot];
                if s.hw.gen == gen && s.hw.frame_end.is_some() {
                    let gap = now.saturating_sub(s.last_valid);
                    if s.last_valid != 0 && gap > s.max_gap {
                        s.max_gap = gap;
                    }
                    s.last_valid = now;
                }
            }
            HwEv::FeedTimer => {
                self.pend_feed = true;
                self.hw_at(self.now + self.cfg.feed_period_ns, HwEv::FeedTimer);
            }
            HwEv::IwdgExpire { deadline } => {
                if deadline == self.deadline && self.iwdg_reset_at.is_none() {
                    self.iwdg_reset_at = Some(self.now);
                    self.mark(-1, "iwdg_reset", 0);
                }
            }
            HwEv::Stop => self.stop = true,
        }
    }

    // ------------------------------------------------------------------------------
    // Efectos de cada paso
    // ------------------------------------------------------------------------------

    fn costs(&self) -> (u64, u64, u64, u64, u64) {
        // (read, pre, close, arm, post) en ciclos. EN-PLACA.md: leer 139, cerrar 10, armar 617, resto ~410
        // con caches calientes; leer 268, cerrar 31, armar 605, total 1 528 con la D-cache desalojada.
        if self.cfg.cold {
            (268, 312, 31, 605, 312)
        } else {
            (139, 205, 10, 617, 205)
        }
    }

    fn tic_next_slot(&mut self, from: usize, job: &mut Job) {
        let mut n = from;
        while n < N && !self.s[n].on {
            n += 1;
        }
        if n >= N {
            job.push_back(cy(50), false, Fx::TicEnd);
            return;
        }
        let (read, pre, _, _, _) = self.costs();
        let armada = matches!(self.s[n].tic.estado(), Estado::Armada { .. });
        let c = if self.s[n].sucia {
            40
        } else if armada {
            read + pre
        } else {
            30 + pre
        };
        job.push_back(cy(c), false, Fx::TicRead(n));
    }

    fn ring_push(&mut self, n: usize, e: Evento) {
        let ok = self.s[n].anillo.empujar(e);
        if ok {
            let s = &mut self.s[n];
            s.ring_occ += 1;
            if s.ring_occ > s.ring_max {
                s.ring_max = s.ring_occ;
            }
            let o = s.ring_occ;
            if o > self.ring_hist_max {
                self.ring_hist_max = o;
            }
        } else {
            self.s[n].ring_lost += 1;
            self.mark(n as i32, "ANILLO_LLENO_descarta", codigo(e) as i64);
        }
    }

    fn apply(&mut self, fx: Fx, job: &mut Job) {
        let now = self.now;
        match fx {
            Fx::None | Fx::P2End => {}
            // ---------------- el tic ----------------
            Fx::TicEntry => {
                self.tic_t0 = now;
                let retraso = ((now - self.last_uev) / 1000) as u32;
                if retraso > 10 {
                    self.tics_tard += 1;
                }
                if retraso > self.retraso_max_us {
                    self.retraso_max_us = retraso;
                }
                let cyc = ((now as f64) * 0.8) as u64 as u32;
                let delta = cyc.wrapping_sub(self.ultima_entrada);
                self.ultima_entrada = cyc;
                self.tics_fus += tics_fusionados(delta, 100_000);
                self.tics = self.tics.wrapping_add(1);
                self.tic_next_slot(0, job);
            }
            Fx::TicRead(n) => {
                if self.s[n].sucia {
                    self.s[n].scratch = None;
                    job.push_back(0, false, Fx::TicPost(n));
                    return;
                }
                let antes = self.s[n].tic.estado();
                let lectura = if matches!(antes, Estado::Armada { .. }) {
                    self.lee(n)
                } else {
                    Lectura::default()
                };
                let gap = self.cfg.gap_ns;
                let t0 = self.tic_t0;
                let s = &mut self.s[n];
                let bajada = s.buzon.fresca().map(|c| s.meta[c].0);
                let (en_curso, hecho) =
                    if matches!(antes, Estado::Vencida { .. } | Estado::Reiniciando { .. }) {
                        (s.rec_en_curso, s.rec_hecha && t0.wrapping_sub(s.rec_t_hecha) >= gap)
                    } else {
                        (false, false)
                    };
                let sal = s.tic.paso(Entrada {
                    lectura,
                    identidad: true,
                    bajada,
                    reinicio_en_curso: en_curso,
                    reinicio_hecho: hecho,
                });
                s.scratch = Some((antes, sal));
                let (_, _, close, arm, post) = self.costs();
                if sal.cerrar {
                    job.push_back(cy(close), false, Fx::TicClose(n));
                }
                if sal.armar {
                    job.push_back(cy(arm), false, Fx::TicArm(n));
                }
                let any = sal.cerrar || sal.armar || sal.eventos[0].is_some() || sal.aviso.is_some();
                job.push_back(cy(if any { post } else { 65 }), false, Fx::TicPost(n));
            }
            Fx::TicClose(n) => {
                self.hw_cierra(n);
                let (_, sal) = self.s[n].scratch.unwrap();
                if sal.eventos[0] == Some(Evento::GiroOk) {
                    let s = &mut self.s[n];
                    s.largo_subida = s.largo;
                    s.subida.publicar(s.rx_actual as usize);
                    s.rx_actual ^= 1;
                    s.giros += 1;
                }
            }
            Fx::TicArm(n) => {
                if let Some(c) = self.s[n].buzon.consumir() {
                    let (_, largo) = self.s[n].meta[c];
                    self.s[n].largo = largo;
                    self.hw_arma(n, largo);
                    self.s[n].sellos += 1;
                    if self.trace_arm == Some(n) {
                        self.mark(n as i32, "cstart", 0);
                    }
                }
            }
            Fx::TicPost(n) => {
                if let Some((antes, sal)) = self.s[n].scratch.take() {
                    for e in sal.eventos.into_iter().flatten() {
                        if e == Evento::PlazoVencido {
                            self.s[n].plazos += 1;
                            self.mark(n as i32, "tic_vencida", 0);
                            if let Some((hn, durs)) = self.hold_on_vencida.clone() {
                                if hn == n {
                                    self.hold_on_vencida = None;
                                    for d in durs {
                                        self.pend_p2.push_back(d);
                                    }
                                }
                            }
                        }
                        self.ring_push(n, e);
                    }
                    let s = &mut self.s[n];
                    match sal.aviso {
                        Some(Aviso::SinBajada) => s.sin_bajada += 1,
                        Some(Aviso::ErrorDma) => s.errores_dma += 1,
                        Some(Aviso::RanuraMuerta) => {
                            s.muertas += 1;
                            self.mark(n as i32, "muerta", 0);
                        }
                        None => {}
                    }
                    let fuera =
                        |e: Estado| matches!(e, Estado::Vencida { .. } | Estado::Reiniciando { .. });
                    let s = &mut self.s[n];
                    if fuera(antes) && !fuera(s.tic.estado()) {
                        s.rec_hecha = false;
                        s.rec_en_curso = false;
                    }
                }
                self.tic_next_slot(n + 1, job);
            }
            Fx::TicEnd => {
                self.pend_plan = true;
            }
            // ---------------- el planificador ----------------
            Fx::PlanEntry => {
                let tics = self.reloj.extiende(self.tics);
                self.plan_now_us = tics * PERIODO_NS / 1000;
                self.plan_next(0, job);
            }
            Fx::PlanDrain(n) => {
                self.plan_drain(n);
                let costo = if self.s[n].buzon.fresca().is_none() { 823 } else { 538 };
                let extra = if self.s[n].buzon.fresca().is_none() { self.cfg.plan_extra_ns } else { 0 };
                job.push_back(cy(costo) + extra, false, Fx::PlanCompose(n));
            }
            Fx::PlanCompose(n) => {
                self.plan_compose(n);
                self.plan_next(n + 1, job);
            }
            Fx::PlanEnd => {}
            // ---------------- la recuperacion ----------------
            Fx::RecEntry => {
                job.push_back(cy(20), false, Fx::RecScan(0));
            }
            Fx::RecScan(n) => {
                if self.s[n].rec_pedida {
                    self.s[n].rec_pedida = false;
                    if n + 1 < N {
                        job.push_front(cy(20), false, Fx::RecScan(n + 1));
                    }
                    job.push_front(0, false, Fx::RecStart(n));
                } else if n + 1 < N {
                    job.push_back(cy(20), false, Fx::RecScan(n + 1));
                }
            }
            Fx::RecStart(n) => {
                self.s[n].rec_en_curso = true;
                self.mark(n as i32, "rec_inicio", 0);
                job.push_front(cy(100), false, Fx::RecSusp(n));
            }
            Fx::RecSusp(n) => {
                let susp = self.cfg.susp_ns;
                let s = &mut self.s[n];
                s.inicio_susp = now;
                s.hw.suspf_at = Some(now + susp);
                job.push_front(cy(180), false, Fx::RecPoll(n));
            }
            Fx::RecPoll(n) => {
                let paradas =
                    !self.chan_stuck_now(n) && self.s[n].hw.suspf_at.map_or(false, |t| now >= t);
                let elapsed = now - self.s[n].inicio_susp;
                if paradas {
                    job.push_front(cy(100), false, Fx::RecResetCh(n));
                } else if elapsed >= self.cfg.t_canal_ns {
                    // la ultima lectura antes de rendirse (hallazgo 6): mismo instante, mismo resultado
                    self.mark(n as i32, "rec_canal_no_para", elapsed as i64);
                    job.push_front(cy(50), false, Fx::RecDecide(n));
                } else {
                    job.push_front(cy(180), false, Fx::RecPoll(n));
                }
            }
            Fx::RecResetCh(n) => {
                job.push_front(1_200, true, Fx::SpiReset(n));
            }
            Fx::RecDecide(n) => {
                let deny = match self.cfg.budget {
                    Budget::Ninguno => false,
                    Budget::V3 { max, ventana_tics, .. } => {
                        self.stamps.len() >= max
                            && self.tics.wrapping_sub(self.stamps[self.stamps.len() - max]) < ventana_tics
                    }
                };
                if deny {
                    self.denegadas += 1;
                    self.mark(n as i32, "escalada_DENEGADA", 0);
                    job.push_front(cy(100), false, Fx::DenyKill(n));
                } else {
                    if let Budget::V3 { .. } = self.cfg.budget {
                        self.stamps.push(self.tics);
                    }
                    job.push_front(cy(100), false, Fx::EscPrep(n));
                }
            }
            Fx::EscPrep(n) => {
                self.escaladas += 1;
                self.esc_times.push(now);
                self.mark(n as i32, "escalada", self.escaladas as i64);
                self.in_esc += 1;
                if self.in_esc > self.max_concurrent_esc {
                    self.max_concurrent_esc = self.in_esc;
                }
                job.push_front(770, true, Fx::EscCrit(n));
            }
            Fx::EscCrit(n) => {
                self.hw_gpdma_reset();
                for k in 0..N {
                    if !self.s[k].on {
                        continue;
                    }
                    self.s[k].sucia = true;
                    if let Some(ev) = self.s[k].tic.declarar_vencida() {
                        self.s[k].colateral += 1;
                        self.s[k].plazos += 1;
                        self.ring_push(k, ev);
                    }
                }
                if let Some(jobs) = self.hold_on_escalada.take() {
                    for j in jobs {
                        self.pend_p2.push_back(j);
                    }
                }
                // las reprogramaciones, una tras otra, en el orden de `escala()`
                for k in (0..N).rev() {
                    if self.s[k].on {
                        job.push_front(1_900, false, Fx::EscProg(n, k));
                    }
                }
            }
            Fx::EscProg(n, k) => {
                self.s[k].sucia = false;
                if (k + 1..N).all(|j| !self.s[j].on) {
                    job.push_front(cy(20), false, Fx::EscEnd(n));
                }
            }
            Fx::EscEnd(n) => {
                self.in_esc -= 1;
                self.pend_plan = true;
                job.push_front(1_200, true, Fx::SpiReset(n));
            }
            Fx::SpiReset(n) => {
                self.hw_spi_reset(n);
                self.mark(n as i32, "spi_reset", 0);
                job.push_front(3_800, false, Fx::RecProg(n));
            }
            Fx::RecProg(n) => {
                job.push_front(cy(100), false, Fx::RecDone(n));
            }
            Fx::RecDone(n) => {
                let s = &mut self.s[n];
                s.rec_t_hecha = now;
                s.rec_hecha = true;
                s.recuperaciones += 1;
                self.mark(n as i32, "rec_hecha", 0);
            }
            Fx::DenyKill(n) => match self.cfg.deny {
                Deny::Retener => {
                    self.s[n].denied = true;
                }
                Deny::Directo => {
                    self.s[n].tic.forzar_muerta();
                    self.s[n].muertas += 1;
                    self.mark(n as i32, "muerta_por_presupuesto", 0);
                }
            },
            // ---------------- el supervisor del IWDG (hilo) ----------------
            Fx::Feeder => {
                let mut ok = true;
                for n in 0..N {
                    if self.s[n].on {
                        if self.s[n].sellos == self.last_seen[n] {
                            ok = false;
                        }
                        self.last_seen[n] = self.s[n].sellos;
                    }
                }
                if ok {
                    self.fed_at = now;
                    self.deadline = now + self.cfg.iwdg_ns;
                    let d = self.deadline;
                    self.hw_at(d, HwEv::IwdgExpire { deadline: d });
                } else if self.first_refusal.is_none() {
                    self.first_refusal = Some(now);
                    self.mark(-1, "supervisor_deja_de_alimentar", 0);
                }
            }
        }
    }

    fn plan_next(&mut self, from: usize, job: &mut Job) {
        let mut n = from;
        while n < N && !self.s[n].on {
            n += 1;
        }
        if n >= N {
            job.push_back(0, false, Fx::PlanEnd);
        } else {
            job.push_back(0, false, Fx::PlanDrain(n));
        }
    }

    fn plan_drain(&mut self, n: usize) {
        let ahora = self.plan_now_us;
        let mut hubo = false;
        loop {
            let ev = match self.s[n].anillo.sacar() {
                Some(e) => e,
                None => break,
            };
            self.s[n].ring_occ = self.s[n].ring_occ.saturating_sub(1);
            hubo = true;
            match ev {
                Evento::GiroOk => {
                    let _ = self.s[n].pol.paso(Evento::GiroOk, ahora);
                    let lect = self.s[n].subida.leer(|_c| {});
                    if let LecSubida::Nueva(_) = lect {
                        let _ = self.s[n].pol.paso(Evento::SubidaOk, ahora);
                    }
                }
                Evento::PlazoVencido => {
                    if self.s[n].pol.paso(ev, ahora) == Accion::Reiniciar {
                        self.s[n].rec_pedida = true;
                        self.pend_rec = true;
                        self.mark(n as i32, "plan_pide_rec", 0);
                    }
                }
                otro => {
                    let _ = self.s[n].pol.paso(otro, ahora);
                }
            }
        }
        if !hubo {
            let _ = self.s[n].pol.paso(Evento::Tick, ahora);
        }
    }

    fn plan_compose(&mut self, n: usize) {
        if self.s[n].buzon.fresca().is_some() {
            return;
        }
        let k = self.s[n].composes;
        let bytes = self.bytes_for(n, k);
        let plazo = self.plazo_tics(bytes);
        let s = &mut self.s[n];
        let c = s.buzon.casilla_escritura();
        s.meta[c] = (plazo, bytes);
        s.buzon.publicar();
        s.composes += 1;
    }
}
