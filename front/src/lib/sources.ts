import type { SourceType, SourceConfig } from "@/types";

export const SOURCES: Record<SourceType, SourceConfig> = {
  arxiv: {
    label: "arXiv",
    color: "bg-[#B31B1B] text-white",
    icon: "FileText",
  },
  github: {
    label: "GitHub",
    color: "bg-[#24292E] text-white",
    icon: "Github",
  },
  huggingface: {
    label: "HuggingFace",
    color: "bg-[#FFD21E] text-black",
    icon: "Bot",
  },
  medium: {
    label: "Medium",
    color: "bg-[#00AB6C] text-white",
    icon: "BookOpen",
  },
  le_monde: {
    label: "Le Monde",
    color: "bg-[#004A9F] text-white",
    icon: "Newspaper",
  },
};

export const ALL_SOURCES = Object.keys(SOURCES) as SourceType[];
