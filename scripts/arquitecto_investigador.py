#!/usr/bin/env python3
"""
🤖 Arquitecto IA - Agente Investigador Autónomo
Investigación diaria de arquitecturas de software e IA (6:00 AM)

Funcionamiento:
1. Busca artículos en múltiples fuentes (ArXiv, GitHub, RSS, etc.)
2. Analiza tendencias y patrones emergentes
3. Genera reporte en Markdown
4. Actualiza el skill 'arquitecto-ia-investigador'
5. Guarda datos en JSON para análisis histórico

Uso:
  python3 scripts/arquitecto_investigador.py

Cron (6:00 AM daily):
  0 6 * * * cd /ruta/proyecto && python3 scripts/arquitecto_investigador.py >> logs/arquitecto.log 2>&1
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import re

# Añadir path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class ArquitectoInvestigador:
    """Agente investigador autónomo de arquitecturas de IA"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or PROJECT_ROOT / "knowledge_base")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = PROJECT_ROOT / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.today = datetime.now()
        # Ubicación del skill (puede estar en diferentes lugares según instalación)
        self.skill_paths = [
            PROJECT_ROOT / "skills" / "arquitecto-ia-investigador" / "SKILL.md",
            Path("/opt/data/skills/devops/arquitecto-ia-investigador/SKILL.md"),
            Path.home() / ".hermes" / "skills" / "arquitecto-ia-investigador" / "SKILL.md",
        ]
        self.today_str = self.today.strftime("%Y-%m-%d")
        self.yesterday = (self.today - timedelta(days=1)).strftime("%Y-%m-%d")

        # Fuentes de investigación
        self.fuentes = {
            "arxiv": {
                "url": "http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL&start=0&max_results=15&sortBy=submittedDate&sortOrder=descending",
                "type": "paper"
            },
            "github_trends": {
                "url": "https://api.github.com/search/repositories?q=ai+OR+llm+OR+mlops+created:>={date}&sort=stars&order=desc&per_page=10",
                "type": "repo"
            },
            "papers_with_code": {
                "url": "https://paperswithcode.com/api/v1/papers/?q=llm+OR+transformer+OR+agent&page=1&items_per_page=10",
                "type": "paper"
            }
        }

        # Keywords para detección de tendencias
        self.keyword_patterns = [
            r"RAG|retrieval.*augmented|vector.*database",
            r"LLM|large.*language.*model|transformer",
            r"agent|multi-agent|autonomous.*agent",
            r"orchestration|pipeline|workflow",
            r"MLOps|model.*serving|inference",
            r"fine-tuning|LoRA|QLoRA|PEFT",
            r"quantization|GPTQ|AWQ|GGUF",
            r"embedding|vector.*search|hybrid.*search",
            r"guardrail|safety|moderation",
            r"observability|monitoring|tracing",
            r"LangChain|LlamaIndex|DSPy|AutoGen|CrewAI",
            r"vLLM|Triton|TensorRT|ONNX",
            r"few-shot|prompt.*engineering|chain.*of.*thought",
            r"graph.*rag|knowledge.*graph",
            r"continual.*learning|online.*learning",
            r"federated.*learning|privacy",
            r"multimodal|vision.*language",
            r"reasoning|chain-of-thought|tree-of-thoughts"
        ]

    def log(self, message: str, level: str = "INFO"):
        """Logging estructurado"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

        # También escribir a archivo de log
        log_file = self.logs_dir / f"arquitecto_{self.today_str}.log"
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {level}: {message}\n")

    def fetch_arxiv_papers(self) -> List[Dict]:
        """Obtiene papers recientes de ArXiv"""
        self.log("📡 Buscando papers en ArXiv...")
        papers = []

        try:
            url = self.fuentes["arxiv"]["url"]
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read().decode('utf-8')

            # Parsear XML de ArXiv
            root = ET.fromstring(data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            for entry in root.findall('atom:entry', ns):
                try:
                    paper = {
                        "source": "arxiv",
                        "title": entry.find('atom:title', ns).text.strip(),
                        "summary": entry.find('atom:summary', ns).text.strip(),
                        "published": entry.find('atom:published', ns).text,
                        "authors": [author.find('atom:name', ns).text
                                   for author in entry.findall('atom:author', ns)],
                        "categories": [cat.get('term') for cat in entry.findall('atom:category', ns)],
                        "url": entry.find('atom:id', ns).text,
                        "pdf_url": entry.find('atom:link[@title="pdf"]', ns).attrib.get('href', '')
                    }
                    papers.append(paper)
                except Exception as e:
                    self.log(f"⚠️ Error parseando paper: {e}", "WARN")

            self.log(f"✅ {len(papers)} papers obtenidos de ArXiv")
        except Exception as e:
            self.log(f"❌ Error conectando a ArXiv: {e}", "ERROR")

        return papers

    def fetch_github_trends(self) -> List[Dict]:
        """Obtiene repositorios trending en GitHub"""
        self.log("🐙 Buscando repositorios trending en GitHub...")
        repos = []

        try:
            date = self.yesterday
            url = self.fuentes["github_trends"]["url"].format(date=date)

            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Arquitecto-IA-Investigator/1.0"
                }
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            for repo in data.get("items", []):
                repos.append({
                    "source": "github",
                    "name": repo["full_name"],
                    "description": repo.get("description", ""),
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "language": repo.get("language", ""),
                    "topics": repo.get("topics", []),
                    "created_at": repo["created_at"],
                    "pushed_at": repo["pushed_at"]
                })

            self.log(f"✅ {len(repos)} repositorios obtenidos de GitHub")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                self.log("⚠️ GitHub API rate limit exceeded (60 req/h). Continuando...", "WARN")
            else:
                self.log(f"❌ Error GitHub API: {e.code}", "ERROR")
        except Exception as e:
            self.log(f"❌ Error conectando a GitHub: {e}", "ERROR")

        return repos

    def fetch_papers_with_code(self) -> List[Dict]:
        """Obtiene papers de Papers With Code"""
        self.log("📄 Buscando en Papers With Code...")
        papers = []

        try:
            url = self.fuentes["papers_with_code"]["url"]
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            for paper in data.get("results", []):
                papers.append({
                    "source": "papers_with_code",
                    "title": paper.get("title", ""),
                    "abstract": paper.get("abstract", ""),
                    "url": paper.get("paper_url", ""),
                    "code_url": paper.get("code_url", ""),
                    "published": paper.get("published", ""),
                    "tasks": paper.get("tasks", []),
                    "stars": paper.get("stars", 0)
                })

            self.log(f"✅ {len(papers)} papers obtenidos de Papers With Code")
        except Exception as e:
            self.log(f"❌ Error Papers With Code: {e}", "ERROR")

        return papers

    def extract_keywords(self, items: List[Dict]) -> Dict[str, int]:
        """Extrae keywords de los artículos y cuenta frecuencia"""
        keyword_counts = {}

        for item in items:
            text = ""
            if "title" in item:
                text += item["title"] + " "
            if "summary" in item:
                text += item["summary"] + " "
            if "description" in item:
                text += item["description"] + " "
            if "abstract" in item:
                text += item["abstract"] + " "

            # Buscar patrones de keywords
            for pattern in self.keyword_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    keyword = pattern.split("|")[0]  # Tomar primera alternativa
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Ordenar por frecuencia
        return dict(sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True))

    def detect_new_frameworks(self, items: List[Dict]) -> List[Dict]:
        """Detecta frameworks/herramientas nuevas mencionadas"""
        framework_patterns = [
            r"LangChain|LlamaIndex|DSPy|AutoGen|CrewAI|LangGraph",
            r"Haystack|Semantic Kernel|RAG|Agent",
            r"vLLM|Triton|BentoML|KServe|TorchServe",
            r"Feast|Hopsworks|Tecton|Feature Store",
            r"Airflow|Prefect|Dagster|Kubeflow|Metaflow",
            r"MLflow|Neptune|Weights & Biases|DVC",
            r"Evidently|Arize|WhyLabs|Fiddler",
            r"Qdrant|Weaviate|Pinecone|Milvus|pgvector"
        ]

        detected = {}
        for item in items:
            text = item.get("title", "") + " " + item.get("description", "")
            for pattern in framework_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match not in detected:
                        detected[match] = {
                            "name": match,
                            "first_seen": self.today_str,
                            "count": 1,
                            "url": item.get("url", "")
                        }
                    else:
                        detected[match]["count"] += 1

        return list(detected.values())

    def identify_patterns(self, items: List[Dict]) -> List[Dict]:
        """Identifica patrones arquitectónicos emergentes"""
        pattern_keywords = {
            "RAG Avanzado": ["hybrid search", "reranking", "compression", "multi-vector"],
            "Agentic Workflows": ["agent", "orchestration", "multi-agent", "autonomous"],
            "Prompt Engineering": ["few-shot", "chain-of-thought", "tree-of-thoughts", "reasoning"],
            "Model Optimization": ["quantization", "pruning", "distillation", "GGUF", "GPTQ"],
            "Observability": ["monitoring", "tracing", "evaluation", "metrics"],
            "Security & Safety": ["guardrail", "moderation", "PII", "adversarial"]
        }

        detected_patterns = []
        for pattern_name, keywords in pattern_keywords.items():
            count = 0
            for item in items:
                text = (item.get("title", "") + " " +
                       item.get("summary", "") + " " +
                       item.get("description", "")).lower()
                for kw in keywords:
                    if kw.lower() in text:
                        count += 1
                        break

            if count >= 2:  # Al menos 2 artículos mencionan el patrón
                detected_patterns.append({
                    "name": pattern_name,
                    "frequency": count,
                    "description": f"Patrón detectado en {count} artículos",
                    "keywords": keywords
                })

        return detected_patterns

    def generate_markdown_report(self, papers: List[Dict], repos: List[Dict],
                                 pwc_papers: List[Dict], keywords: Dict,
                                 frameworks: List[Dict], patterns: List[Dict]) -> str:
        """Genera reporte en Markdown"""
        self.log("📝 Generando reporte Markdown...")

        md = f"""# 🏛️ Reporte Diario de Arquitectura de IA

**Fecha**: {self.today_str}
**Generado por**: Arquitecto IA Investigador (automático)
**Fuentes consultadas**: ArXiv ({len(papers)}), GitHub ({len(repos)}), Papers With Code ({len(pwc_papers)})

---

## 📊 Resumen Ejecutivo

- **Total artículos analizados**: {len(papers) + len(repos) + len(pwc_papers)}
- **Tendencias principales**: {", ".join(list(keywords.keys())[:5])}
- **Frameworks detectados**: {len(frameworks)}
- **Patrones emergentes**: {len(patterns)}

---

## 🎯 Top 5 Tendencias del Día

"""
        for i, (kw, count) in enumerate(list(keywords.items())[:5], 1):
            md += f"{i}. **{kw}** (mencionado {count} veces)\n"

        md += "\n## 🆕 Frameworks/Herramientas Detectadas\n\n"
        if frameworks:
            for fw in sorted(frameworks, key=lambda x: x["count"], reverse=True)[:10]:
                md += f"- **{fw['name']}**: {fw['count']} menciones\n"
        else:
            md += "_No se detectaron frameworks nuevos hoy._\n"

        md += "\n## 📈 Patrones Arquitectónicos Emergentes\n\n"
        if patterns:
            for pattern in patterns:
                md += f"### {pattern['name']}\n"
                md += f"**Frecuencia**: {pattern['frequency']} artículos\n"
                md += f"**Keywords**: {', '.join(pattern['keywords'][:3])}\n\n"
        else:
            md += "_No se detectaron patrones nuevos hoy._\n"

        md += "\n## 📚 Artículos Recientes (ArXiv)\n\n"
        if papers:
            for paper in papers[:5]:
                md += f"### {paper['title']}\n"
                md += f"- **Autores**: {', '.join(paper['authors'][:3])}\n"
                md += f"- **Categorías**: {', '.join(paper['categories'][:3])}\n"
                md += f"- **URL**: {paper['url']}\n"
                if paper['pdf_url']:
                    md += f"- **PDF**: {paper['pdf_url']}\n"
                md += f"- **Resumen**: {paper['summary'][:300]}...\n\n"
        else:
            md += "_No se obtuvieron papers de ArXiv._\n"

        md += "\n## 🐙 Repositorios Trending (GitHub)\n\n"
        if repos:
            for repo in repos[:5]:
                md += f"### [{repo['name']}]({repo['url']})\n"
                md += f"- **⭐ Stars**: {repo['stars']}\n"
                md += f"- **Lenguaje**: {repo['language']}\n"
                md += f"- **Descripción**: {repo['description'] or 'Sin descripción'}\n"
                md += f"- **Creado**: {repo['created_at'][:10]}\n\n"
        else:
            md += "_No se obtuvieron repositorios trending._\n"

        md += f"\n## 📊 Métricas de Calidad\n\n"
        md += f"- **Fuentes activas**: {len([f for f in [papers, repos, pwc_papers] if f])}/3\n"
        md += f"- **Papers con código**: {sum(1 for p in pwc_papers if p.get('code_url'))}\n"
        md += f"- **Diversidad de fuentes**: {'Alta' if len(papers) > 0 and len(repos) > 0 else 'Media'}\n"

        md += f"\n---\n\n*Reporte generado automáticamente a las {datetime.now().strftime('%H:%M:%S')}*"

        return md

    def save_results(self, data: Dict):
        """Guarda resultados en JSON y Markdown"""
        # Guardar JSON completo
        json_path = self.output_dir / f"investigacion_{self.today_str}.json"
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.log(f"💾 JSON guardado: {json_path}")

        # Guardar Markdown
        md_path = self.output_dir / f"reporte_{self.today_str}.md"
        with open(md_path, "w", encoding='utf-8') as f:
            f.write(data["report"])
        self.log(f"📄 Reporte guardado: {md_path}")

    def update_skill(self, data: Dict):
        """Actualiza el skill con la nueva información"""
        self.log("🔄 Actualizando skill 'arquitecto-ia-investigador'...")

        # Buscar skill en múltiples ubicaciones posibles
        skill_md = None
        for path in self.skill_paths:
            if path.exists():
                skill_md = path
                self.log(f"✅ Skill encontrado en: {path}")
                break

        if not skill_md:
            self.log("⚠️ Skill no encontrado en ninguna ubicación known. No se actualizará", "WARN")
            # Intentar buscar recursivamente desde /opt/data
            import subprocess
            try:
                result = subprocess.run(
                    ["find", "/opt/data", "-name", "SKILL.md", "-path", "*arquitecto*"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    skill_md = Path(result.stdout.strip().split('\n')[0])
                    self.log(f"✅ Skill encontrado via búsqueda: {skill_md}")
            except Exception as e:
                self.log(f"⚠️ Búsqueda fallida: {e}", "WARN")

        if not skill_md:
            return

        # Leer skill actual
        content = skill_md.read_text(encoding='utf-8')

        # Generar sección de actualización
        nueva_seccion = self._generate_update_section(data)

        # Insertar antes del cierre
        last_section_match = list(re.finditer(r'\n## ', content))
        if last_section_match:
            insert_pos = last_section_match[-1].start()
        else:
            insert_pos = len(content)

        new_content = content[:insert_pos] + nueva_seccion + content[insert_pos:]

        # Escribir actualizado
        skill_md.write_text(new_content, encoding='utf-8')
        self.log(f"✅ Skill actualizado: {skill_md}")

    def _generate_update_section(self, data: Dict) -> str:
        """Genera la sección de actualización para el skill"""
        fecha = self.today_str
        total = data['total_articles']
        top_keywords = ", ".join(list(data['keywords'].keys())[:5])
        new_fw = len(data['new_frameworks'])
        new_patterns = len(data['patterns'])

        section = f"""

---

## 📅 Actualización Automática - {fecha}

### 📊 Resumen del Día
- **Artículos analizados**: {total}
- **Keywords top**: {top_keywords}
- **Frameworks detectados**: {new_fw}
- **Patrones nuevos**: {new_patterns}

### 🔥 Tendencias Detectadas
"""
        for kw, count in list(data['keywords'].items())[:8]:
            section += f"- `{kw}`: {count} menciones\n"

        if data['new_frameworks']:
            section += "\n### 🆕 Frameworks/Herramientas\n"
            for fw in sorted(data['new_frameworks'], key=lambda x: x['count'], reverse=True)[:5]:
                section += f"- **{fw['name']}** ({fw['count']} menciones)\n"

        if data['patterns']:
            section += "\n### 🧠 Patrones Arquitectónicos\n"
            for pattern in data['patterns'][:5]:
                section += f"- **{pattern['name']}**: {pattern['description']}\n"

        section += f"""

**Reporte completo**: `knowledge_base/reporte_{fecha}.md`
**Datos brutos**: `knowledge_base/investigacion_{fecha}.json`

---
"""
        return section

    def run(self):
        """Pipeline principal de ejecución"""
        self.log("🚀 Iniciando investigación diaria de arquitectura IA")
        self.log("=" * 60)

        # 1. Obtener datos de todas las fuentes
        papers = self.fetch_arxiv_papers()
        repos = self.fetch_github_trends()
        pwc_papers = self.fetch_papers_with_code()

        all_items = papers + repos + pwc_papers

        if not all_items:
            self.log("⚠️ No se obtuvieron datos de ninguna fuente", "WARN")

        # 2. Analizar
        self.log("🔍 Analizando datos obtenidos...")
        keywords = self.extract_keywords(all_items)
        frameworks = self.detect_new_frameworks(all_items)
        patterns = self.identify_patterns(all_items)

        # 3. Generar reporte
        report = self.generate_markdown_report(
            papers, repos, pwc_papers, keywords, frameworks, patterns
        )

        # 4. Preparar datos completos
        data = {
            "date": self.today_str,
            "sources": {
                "arxiv_count": len(papers),
                "github_count": len(repos),
                "papers_with_code_count": len(pwc_papers)
            },
            "total_articles": len(all_items),
            "keywords": keywords,
            "new_frameworks": frameworks,
            "patterns": patterns,
            "articles": {
                "arxiv": papers[:3],
                "github": repos[:3],
                "papers_with_code": pwc_papers[:3]
            },
            "report": report
        }

        # 5. Guardar
        self.save_results(data)

        # 6. Actualizar skill
        self.update_skill(data)

        # 7. Estadísticas finales
        self.log("=" * 60)
        self.log("✅ Investigación completada exitosamente!")
        self.log(f"   - {len(papers)} papers académicos")
        self.log(f"   - {len(repos)} repositorios GitHub")
        self.log(f"   - {len(pwc_papers)} papers con código")
        self.log(f"   - {len(keywords)} keywords únicas")
        self.log(f"   - {len(frameworks)} frameworks detectados")
        self.log(f"   - Reporte: knowledge_base/reporte_{self.today_str}.md")

        return data

def main():
    """Punto de entrada principal"""
    try:
        investigator = ArquitectoInvestigador()
        results = investigator.run()

        # Salida para cron (opcional)
        print("\n" + "=" * 60)
        print("📊 RESUMEN PARA CRON:")
        print(f"Fecha: {results['date']}")
        print(f"Artículos: {results['total_articles']}")
        print(f"Tendencias: {len(results['keywords'])}")
        print(f"Frameworks: {len(results['new_frameworks'])}")
        print(f"Patrones: {len(results['patterns'])}")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️ Ejecución interrumpida por usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
