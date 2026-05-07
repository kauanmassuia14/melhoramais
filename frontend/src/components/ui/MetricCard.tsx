"use client";

import { useState, useRef, useEffect } from "react";
import { QuestionMarkCircleIcon, XMarkIcon } from "@heroicons/react/24/outline";
import { InformationCircleIcon } from "@heroicons/react/24/solid";

// ─── Dicionário completo das métricas ───────────────────────────────────────
export const METRIC_INFO: Record<string, {
  fullName: string;
  unit?: string;
  description: string;
  formula: string;
  interpretation: string;
  color: string;
}> = {
  iabczg: {
    fullName: "Índice ABCZ Global",
    description:
      "Índice composto que resume a capacidade genética global do animal, combinando todas as DEPs ponderadas por seus pesos econômicos na raça Zebuína. Quanto maior, melhor é o potencial genético agregado.",
    formula:
      "Combinação ponderada de todas as DEPs (PN, PD, PA, PS, PM, IPP, STAY, PE365, AOL, ACAB, MAR) multiplicadas pelos seus respectivos valores econômicos relativos.",
    interpretation:
      "D1 (top 10%): excelente • D5 (mediana): médio • D10 (inferior 10%): abaixo da média. Animais D1 são candidatos prioritários a reprodutores.",
    color: "cyan",
  },
  deca: {
    fullName: "Decil (DECA)",
    description:
      "Posição relativa do animal dentro da raça, dividida em 10 grupos (decis) com base no índice global. D1 representa os 10% melhores animais avaliados.",
    formula:
      "Ordenação do iABCZg de todos os animais avaliados, dividida em 10 faixas percentuais iguais.",
    interpretation:
      "D1: top 10% (elite) • D2: top 20% • … • D10: 10% inferiores. Para seleção de reprodutores, priorize D1 e D2.",
    color: "violet",
  },
  pn: {
    fullName: "DEP Peso ao Nascimento (PN-EDg)",
    unit: "kg",
    description:
      "Diferença Esperada na Progênie para o Peso ao Nascimento. Indica quantos kg a mais (ou a menos) os filhos deste animal terão ao nascer em relação à média da raça.",
    formula:
      "DEP_PN = (média dos filhos em campo) − (média da raça no mesmo grupo contemporâneo), ajustado por acurácia.",
    interpretation:
      "Valores positivos aumentam o peso ao nascer (cuidado com partos difíceis em fêmeas). Valores negativos reduzem — desejável em acasalamentos com novilhas.",
    color: "amber",
  },
  pd: {
    fullName: "DEP Peso à Desmama (PD-EDg)",
    unit: "kg",
    description:
      "Diferença Esperada na Progênie para o Peso à Desmama (~210 dias). Mede o potencial genético para crescimento precoce até a desmama.",
    formula:
      "DEP_PD = média ajustada dos filhos ao P210 − média do grupo contemporâneo, ponderada pela acurácia de estimativa.",
    interpretation:
      "Cada ponto positivo representa +1 kg esperado nos filhos na desmama. Ex: DEP +15 = espera-se filhos 15 kg mais pesados que a média da raça.",
    color: "amber",
  },
  pa: {
    fullName: "DEP Peso ao Ano (PA-EDg)",
    unit: "kg",
    description:
      "Diferença Esperada na Progênie para o Peso ao Ano (~365 dias). Avalia o potencial de crescimento contínuo após a desmama até 1 ano de idade.",
    formula:
      "DEP_PA = média ajustada dos filhos ao P365 − média do grupo contemporâneo, ponderada pela acurácia.",
    interpretation:
      "Complementa o PD para selecionar animais com bom crescimento pós-desmama. Quando ausente, o animal ainda não possui filhos avaliados nessa faixa.",
    color: "amber",
  },
  ps: {
    fullName: "DEP Peso ao Sobreano (PS-EDg)",
    unit: "kg",
    description:
      "Diferença Esperada na Progênie para o Peso ao Sobreano (~450 dias). Indica o potencial genético para peso na terminação.",
    formula:
      "DEP_PS = média ajustada dos filhos ao P450 − média do grupo contemporâneo.",
    interpretation:
      "Principal indicador para seleção de animais terminados em confinamento ou semi-confinamento. Alto PS = filhos mais pesados ao abate.",
    color: "orange",
  },
  pm: {
    fullName: "DEP Peso da Mãe (PM-EMg)",
    unit: "kg",
    description:
      "Diferença Esperada na Progênie para o efeito materno no peso. Avalia a capacidade materna do animal (para fêmeas) ou das filhas (para machos) em criar bezerros pesados.",
    formula:
      "Separação do efeito materno direto (leite, cuidado) do efeito genético direto de crescimento do bezerro.",
    interpretation:
      "Importante para seleção de matrizes. Alto PM = filhas serão melhores mães, gerando bezerros mais pesados à desmama pela via materna.",
    color: "purple",
  },
  ipp: {
    fullName: "DEP Idade ao Primeiro Parto (IPP)",
    unit: "dias",
    description:
      "Diferença Esperada na Progênie para a Idade ao Primeiro Parto das filhas. Valores negativos são desejáveis — indicam filhas que parem mais cedo.",
    formula:
      "DEP_IPP = média da idade ao 1º parto das filhas − média do grupo contemporâneo. Trait de limiar modelado por regressão linear.",
    interpretation:
      "IPP negativo = filhas parem mais jovens (maior precocidade sexual). Ex: DEP -36 dias = filhas param em média 36 dias mais cedo que a média racial.",
    color: "pink",
  },
  stay: {
    fullName: "DEP Stayability (STAYg)",
    unit: "%",
    description:
      "Probabilidade das filhas do reprodutor de permanecerem no rebanho até os 6 anos, tendo parido até os 4 anos. Mede a longevidade produtiva.",
    formula:
      "Modelo de limiar com distribuição logística. DEP_STAY = probabilidade de permanência das filhas vs. média racial.",
    interpretation:
      "Valores positivos indicam filhas mais longevas e produtivas. Ex: STAY +67 = filhas têm 67% mais probabilidade de permanecer produtivas até os 6 anos.",
    color: "green",
  },
  pe_365: {
    fullName: "DEP Perímetro Escrotal aos 365 dias (PE-365g)",
    unit: "cm",
    description:
      "Diferença Esperada na Progênie para o Perímetro Escrotal mensurado ao ano de idade. Correlacionado com precocidade sexual e fertilidade dos filhos e filhas.",
    formula:
      "DEP_PE365 = média do PE365 dos filhos − média do grupo contemporâneo.",
    interpretation:
      "Alto PE = filhos mais precoces sexualmente e filhas com menor IPP. Indicador importante para melhoramento da eficiência reprodutiva.",
    color: "blue",
  },
  aol: {
    fullName: "DEP Área do Olho de Lombo (AOLg)",
    unit: "cm²",
    description:
      "Diferença Esperada na Progênie para a Área do Olho de Lombo (músculo Longissimus dorsi) por ultrassonografia. Indicador de musculosidade e rendimento de carcaça.",
    formula:
      "DEP_AOL = média do AOL dos filhos ajustado por peso e covariáveis − média do grupo contemporâneo.",
    interpretation:
      "Alto AOL = filhos mais musculosos com maior rendimento de carcaça. Relevante para raças de corte orientadas ao mercado premium.",
    color: "emerald",
  },
  acab: {
    fullName: "DEP Acabamento de Carcaça (ACABg)",
    unit: "mm",
    description:
      "Diferença Esperada na Progênie para a espessura de gordura subcutânea na carcaça. Indica cobertura de gordura para proteção da carcaça no frigorífico.",
    formula:
      "DEP_ACAB = média da EGS dos filhos (em mm, por ultrassom) − média do grupo contemporâneo.",
    interpretation:
      "Valores entre 3–6mm na carcaça são ideais para o mercado brasileiro. Muito baixo = perda de rendimento; muito alto = desconto no frigorífico.",
    color: "yellow",
  },
  marmoreio: {
    fullName: "DEP Marmoreio (MARg)",
    unit: "",
    description:
      "Diferença Esperada na Progênie para o marmoreio intramuscular. Mede a gordura entremeada ao músculo, indicadora de maciez e sabor da carne.",
    formula:
      "Avaliado por ultrassonografia no músculo Longissimus. DEP_MAR = score dos filhos − média contemporânea.",
    interpretation:
      "Alto marmoreio = carne mais macia e saborosa. Essencial para mercados premium (USDA Choice/Prime, Wagyu-crossbred, exportação).",
    color: "rose",
  },
  eg: {
    fullName: "DEP Estrutura Corporal (Eg)",
    unit: "pontos",
    description:
      "Diferença Esperada na Progênie para a estrutura corporal do animal, avaliada por escores visuais padronizados (conformação, ossatura, profundidade).",
    formula:
      "Média dos escores de conformação dos filhos avaliados em campo, ajustados por grupo contemporâneo.",
    interpretation:
      "Animais com alta DEP Estrutura tendem a ter filhos mais harmoniosos e adaptados para produção eficiente em pastagem.",
    color: "teal",
  },
  pg: {
    fullName: "DEP Precocidade de Acabamento (Pg)",
    unit: "pontos",
    description:
      "Diferença Esperada na Progênie para a precocidade de acabamento de carcaça — capacidade do animal de depositar gordura em idades mais jovens.",
    formula:
      "Score de precocidade dos filhos avaliado em campo (escore 1–5) ajustado por grupo contemporâneo e covariáveis.",
    interpretation:
      "Alta precocidade = filhos atingem o acabamento ideal mais cedo e com menos peso, reduzindo o custo de terminação em confinamento.",
    color: "orange",
  },
  mg: {
    fullName: "DEP Musculosidade (Mg)",
    unit: "pontos",
    description:
      "Diferença Esperada na Progênie para a musculosidade — desenvolvimento muscular geral do animal avaliado por escore visual padronizado.",
    formula:
      "Score de musculosidade dos filhos (escore 1–5) ajustado por grupo contemporâneo.",
    interpretation:
      "Alta musculosidade = filhos com maior proporção de músculo em relação a osso e gordura, melhorando o rendimento de carcaça e o preço por kg.",
    color: "indigo",
  },
};

// ─── Componente principal ────────────────────────────────────────────────────
interface MetricCardProps {
  metricKey: string;
  label: string;
  value: string | number | null | undefined;
  unit?: string;
}

const colorMap: Record<string, string> = {
  cyan: "border-cyan-500/20 bg-cyan-500/5",
  violet: "border-violet-500/20 bg-violet-500/5",
  amber: "border-amber-500/20 bg-amber-500/5",
  orange: "border-orange-500/20 bg-orange-500/5",
  purple: "border-purple-500/20 bg-purple-500/5",
  pink: "border-pink-500/20 bg-pink-500/5",
  green: "border-emerald-500/20 bg-emerald-500/5",
  blue: "border-blue-500/20 bg-blue-500/5",
  emerald: "border-emerald-500/20 bg-emerald-500/5",
  yellow: "border-yellow-500/20 bg-yellow-500/5",
  rose: "border-rose-500/20 bg-rose-500/5",
  teal: "border-teal-500/20 bg-teal-500/5",
  indigo: "border-indigo-500/20 bg-indigo-500/5",
};

const valueColorMap: Record<string, string> = {
  cyan: "text-cyan-300",
  violet: "text-violet-300",
  amber: "text-amber-300",
  orange: "text-orange-300",
  purple: "text-purple-300",
  pink: "text-pink-300",
  green: "text-emerald-300",
  blue: "text-blue-300",
  emerald: "text-emerald-300",
  yellow: "text-yellow-300",
  rose: "text-rose-300",
  teal: "text-teal-300",
  indigo: "text-indigo-300",
};

export function MetricCard({ metricKey, label, value, unit }: MetricCardProps) {
  const info = METRIC_INFO[metricKey];
  const [showTooltip, setShowTooltip] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const colorClass = info ? colorMap[info.color] ?? colorMap.cyan : "border-white/10 bg-white/5";
  const valueClass = info ? valueColorMap[info.color] ?? "text-white" : "text-white";

  const displayValue = value != null && value !== "" ? `${value}${unit ? ` ${unit}` : ""}` : null;

  return (
    <>
      <div className={`relative rounded-xl border p-4 flex flex-col gap-1 ${colorClass}`}>
        {/* Label + help button */}
        <div className="flex items-start justify-between gap-2">
          <span className="text-[10px] text-text-muted uppercase tracking-wider leading-tight">
            {label}
          </span>
          {info && (
            <div className="relative flex-shrink-0">
              <button
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                onClick={() => setShowModal(true)}
                className="w-4 h-4 rounded-full flex items-center justify-center text-text-muted hover:text-white transition-colors"
                aria-label={`Ajuda sobre ${label}`}
              >
                <QuestionMarkCircleIcon className="w-4 h-4" />
              </button>

              {/* Tooltip */}
              {showTooltip && (
                <div
                  ref={tooltipRef}
                  className="absolute right-0 top-6 z-50 w-52 rounded-xl border border-white/10 bg-slate-900/95 backdrop-blur-sm p-3 shadow-2xl pointer-events-none"
                >
                  <p className="text-xs text-text-secondary leading-relaxed">
                    Quer entender essa métrica?
                  </p>
                  <p className="text-xs text-emerald-400 mt-1 font-medium">
                    Clique no ícone para ver a explicação completa →
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Value */}
        <span className={`text-2xl font-bold tracking-tight font-mono ${displayValue ? valueClass : "text-text-muted"}`}>
          {displayValue ?? "—"}
        </span>
      </div>

      {/* Modal */}
      {showModal && info && (
        <MetricModal info={info} label={label} onClose={() => setShowModal(false)} />
      )}
    </>
  );
}

// ─── Modal de explicação ────────────────────────────────────────────────────
function MetricModal({
  info,
  label,
  onClose,
}: {
  info: (typeof METRIC_INFO)[string];
  label: string;
  onClose: () => void;
}) {
  // Fechar com ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const borderColor = colorMap[info.color] ?? colorMap.cyan;
  const textColor = valueColorMap[info.color] ?? "text-white";

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Card */}
      <div
        className={`relative z-10 w-full max-w-lg rounded-2xl border ${borderColor} bg-slate-900/95 backdrop-blur-xl p-6 shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <InformationCircleIcon className={`w-5 h-5 ${textColor}`} />
              <span className={`text-xs font-semibold uppercase tracking-wider ${textColor}`}>
                Explicação da Métrica
              </span>
            </div>
            <h2 className="text-xl font-bold text-white">{info.fullName}</h2>
            <p className="text-xs text-text-muted mt-0.5">{label}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-text-muted hover:text-white hover:bg-white/10 transition-all flex-shrink-0"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* O que é */}
          <section>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
              O que é
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {info.description}
            </p>
          </section>

          {/* Como é calculado */}
          <section className={`rounded-xl border ${borderColor} p-3`}>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
              Como é calculado
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed font-mono text-xs">
              {info.formula}
            </p>
          </section>

          {/* Como interpretar */}
          <section>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
              Como interpretar
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {info.interpretation}
            </p>
          </section>
        </div>

        <button
          onClick={onClose}
          className={`mt-6 w-full py-2.5 rounded-xl text-sm font-medium border ${borderColor} ${textColor} hover:bg-white/5 transition-all`}
        >
          Entendido
        </button>
      </div>
    </div>
  );
}
