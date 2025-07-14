#!/usr/bin/env python3
"""
Dashboard categorizado con análisis inteligente por directorio.
Separa código de producción (/src/) de tests, tools y scripts.
"""
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import threading
import webbrowser
import socket
import ast

# Añadir rutas a las carpetas reorganizadas
sys.path.insert(0, str(Path(__file__).parent.parent / 'code_analysis'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'data_processing'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'god_class_refactor'))

try:
    from smart_code_analyzer import SmartCodeAnalyzer, CodeCategory
    from code_rag_system import CodeRAGSystem
    from god_class_refactor_guide import GodClassRefactorGuide
    HAS_SMART_ANALYSIS = True
    HAS_GOD_CLASS_REFACTOR = True
except ImportError:
    HAS_SMART_ANALYSIS = False
    HAS_GOD_CLASS_REFACTOR = False

class DashboardDataProvider:
    """Proveedor de datos para el dashboard."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metrics_file = project_root / "CODE_METRICS_REPORT.json"
        self._smart_analyzer = None
        self._rag_system = None
        self._god_class_refactor = None
    
    @property
    def smart_analyzer(self):
        """Lazy loading del analizador inteligente."""
        if self._smart_analyzer is None and HAS_SMART_ANALYSIS:
            try:
                self._smart_analyzer = SmartCodeAnalyzer(self.project_root)
            except Exception as e:
                print(f"⚠️ Error inicializando analizador: {e}")
        return self._smart_analyzer
    
    @property
    def rag_system(self):
        """Lazy loading del sistema RAG."""
        if self._rag_system is None:
            try:
                from code_rag_system import CodeRAGSystem
                self._rag_system = CodeRAGSystem(self.project_root)
                self._rag_system.index_codebase()
            except Exception as e:
                print(f"⚠️ Error inicializando RAG: {e}")
        return self._rag_system
    
    @property
    def god_class_refactor(self):
        """Lazy loading del God Class Refactor Guide."""
        if self._god_class_refactor is None and HAS_GOD_CLASS_REFACTOR:
            try:
                self._god_class_refactor = GodClassRefactorGuide()
            except Exception as e:
                print(f"⚠️ Error inicializando God Class Refactor: {e}")
        return self._god_class_refactor
    
    def get_summary_data(self) -> Dict[str, Any]:
        """Obtener datos de resumen."""
        if not self.metrics_file.exists():
            return self._generate_quick_summary()
        
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('summary', {})
        except Exception as e:
            print(f"Error cargando métricas: {e}")
            return self._generate_quick_summary()
    
    def get_smart_analysis_data(self) -> Dict[str, Any]:
        """Obtener análisis inteligente."""
        if not self.smart_analyzer:
            return {'error': 'Análisis inteligente no disponible'}
        
        try:
            categorized = self.smart_analyzer.analyze_project()
            summary = self.smart_analyzer.get_orphan_summary()
            return {
                'categorized': categorized,
                'summary': summary,
                'timestamp': int(time.time())
            }
        except Exception as e:
            return {'error': f'Error en análisis: {e}'}
    
    def _generate_quick_summary(self) -> Dict[str, Any]:
        """Generar resumen rápido sin métricas."""
        return {
            'total_files': len(list(self.project_root.rglob('*.py'))),
            'message': 'Ejecuta análisis completo para métricas detalladas',
            'timestamp': int(time.time())
        }

class DashboardAPIHandler:
    """Manejador de APIs del dashboard."""
    
    def __init__(self, data_provider: DashboardDataProvider):
        self.data_provider = data_provider
    
    def handle_summary(self) -> tuple[int, str, str]:
        """Manejar API de resumen."""
        try:
            summary = self.data_provider.get_summary_data()
            return 200, 'application/json', json.dumps(summary)
        except Exception as e:
            error_data = {'error': f'Error obteniendo resumen: {e}'}
            return 500, 'application/json', json.dumps(error_data)
    
    def handle_smart_analysis(self) -> tuple[int, str, str]:
        """Manejar API de análisis inteligente."""
        try:
            analysis = self.data_provider.get_smart_analysis_data()
            return 200, 'application/json', json.dumps(analysis)
        except Exception as e:
            error_data = {'error': f'Error en análisis inteligente: {e}'}
            return 500, 'application/json', json.dumps(error_data)
    
    def handle_rag_query(self, query: str) -> tuple[int, str, str]:
        """Manejar consultas RAG."""
        if not self.data_provider.rag_system:
            error_data = {'error': 'Sistema RAG no disponible'}
            return 500, 'application/json', json.dumps(error_data)
        
        try:
            result = self.data_provider.rag_system.ask_question(query)
            return 200, 'application/json', json.dumps(result)
        except Exception as e:
            error_data = {'error': f'Error en consulta RAG: {e}'}
            return 500, 'application/json', json.dumps(error_data)
    
    def handle_god_class_detection(self) -> tuple[int, str, str]:
        """Detectar God classes en el proyecto."""
        try:
            god_classes = []
            python_files = list(self.data_provider.project_root.rglob('*.py'))
            
            for file_path in python_files:
                # Solo analizar archivos en src/ por defecto
                if '/src/' in str(file_path):
                    try:
                        # Análisis rápido para detectar God classes
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        import ast
                        tree = ast.parse(content)
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                                if len(methods) >= 10:  # God class threshold
                                    god_classes.append({
                                        'file': str(file_path.relative_to(self.data_provider.project_root)),
                                        'class_name': node.name,
                                        'method_count': len(methods),
                                        'status': 'detected'
                                    })
                    except Exception:
                        continue  # Skip problematic files
            
            result = {
                'god_classes': god_classes,
                'total_detected': len(god_classes),
                'analysis_complete': True
            }
            
            return 200, 'application/json', json.dumps(result)
            
        except Exception as e:
            error_data = {'error': f'Error detectando God classes: {e}'}
            return 500, 'application/json', json.dumps(error_data)
    
    def handle_god_class_analysis(self, file_path: str) -> tuple[int, str, str]:
        """Analizar God class específica con IA."""
        if not self.data_provider.god_class_refactor:
            error_data = {'error': 'God Class Refactor no disponible'}
            return 500, 'application/json', json.dumps(error_data)
        
        try:
            # Convertir path relativo a absoluto
            abs_file_path = self.data_provider.project_root / file_path
            
            if not abs_file_path.exists():
                error_data = {'error': f'Archivo no encontrado: {file_path}'}
                return 404, 'application/json', json.dumps(error_data)
            
            # Ejecutar análisis con IA
            result = self.data_provider.god_class_refactor.analyze_god_class(abs_file_path)
            
            if 'error' in result:
                return 400, 'application/json', json.dumps(result)
            
            # Agregar información adicional para el dashboard
            result['file_path'] = file_path
            result['analysis_timestamp'] = int(time.time())
            
            return 200, 'application/json', json.dumps(result)
            
        except Exception as e:
            error_data = {'error': f'Error analizando God class: {e}'}
            return 500, 'application/json', json.dumps(error_data)

class CategorizedDashboardHandler(BaseHTTPRequestHandler):
    """Handler HTTP para dashboard categorizado (refactorizado)."""
    
    def __init__(self, *args, **kwargs):
        self.project_root = Path(__file__).parent.parent
        self.data_provider = DashboardDataProvider(self.project_root)
        self.api_handler = DashboardAPIHandler(self.data_provider)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Manejar peticiones GET."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/' or path == '/index.html':
            self.serve_categorized_dashboard()
        elif path == '/api/summary':
            status, content_type, content = self.api_handler.handle_summary()
            self._send_response(status, content_type, content)
        elif path == '/api/smart-analysis':
            status, content_type, content = self.api_handler.handle_smart_analysis()
            self._send_response(status, content_type, content)
        elif path == '/api/category-breakdown':
            self.serve_category_breakdown()
        elif path == '/api/orphan-analysis':
            self.serve_orphan_analysis()
        elif path == '/api/ask-code':
            query = query_params.get('q', [''])[0]
            if query:
                status, content_type, content = self.api_handler.handle_rag_query(query)
                self._send_response(status, content_type, content)
            else:
                self.send_error(400, "Parámetro 'q' requerido")
        elif path == '/api/filter-code':
            self.serve_filtered_code(query_params)
        elif path == '/api/god-classes':
            status, content_type, content = self.api_handler.handle_god_class_detection()
            self._send_response(status, content_type, content)
        elif path == '/api/analyze-god-class':
            file_path = query_params.get('file', [''])[0]
            if file_path:
                status, content_type, content = self.api_handler.handle_god_class_analysis(file_path)
                self._send_response(status, content_type, content)
            else:
                self.send_error(400, "Parámetro 'file' requerido")
        else:
            self.send_error(404, "Endpoint no encontrado")
    
    def _send_response(self, status: int, content_type: str, content: str):
        """Enviar respuesta HTTP."""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def send_json_response(self, data: Any):
        """Enviar respuesta JSON."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_html_response(self, html: str):
        """Enviar respuesta HTML."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_categorized_dashboard(self):
        """Servir dashboard categorizado."""
        smart_enabled = "true" if HAS_SMART_ANALYSIS else "false"
        
        # Leer el archivo HTML separado
        dashboard_html_path = Path(__file__).parent / 'dashboard.html'
        try:
            with open(dashboard_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Reemplazar la variable SMART_ENABLED
            html_content = html_content.replace('{{SMART_ENABLED}}', smart_enabled)
            
            return html_content
        except FileNotFoundError:
            return f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Dashboard Categorizado - Scrapper LLM</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(20px);
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .filter-tabs {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        
        .tab {{
            background: #f8f9fa;
            border: 2px solid #ddd;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 500;
        }}
        
        .tab.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .tab.production {{
            border-color: #28a745;
        }}
        
        .tab.production.active {{
            background: #28a745;
        }}
        
        .tab.test {{
            border-color: #ffc107;
        }}
        
        .tab.test.active {{
            background: #ffc107;
            color: #000;
        }}
        
        .tab.tooling {{
            border-color: #17a2b8;
        }}
        
        .tab.tooling.active {{
            background: #17a2b8;
        }}
        
        .tab.god-classes {{
            border-color: #e83e8c;
        }}
        
        .tab.god-classes.active {{
            background: #e83e8c;
            color: white;
        }}
        
        .controls {{
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }}
        
        .btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }}
        
        .btn:hover {{
            background: #45a049;
            transform: translateY(-2px);
        }}
        
        .btn.smart {{
            background: #9C27B0;
        }}
        
        .btn.smart:hover {{
            background: #7B1FA2;
        }}
        
        .rag-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .rag-input {{
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 1.1em;
            outline: none;
            transition: border-color 0.3s;
        }}
        
        .rag-input:focus {{
            border-color: #667eea;
        }}
        
        .filter-hint {{
            background: #e3f2fd;
            border-radius: 10px;
            padding: 10px;
            margin-top: 10px;
            font-size: 0.9em;
            border-left: 4px solid #2196F3;
        }}
        
        .category-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .category-card {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .category-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }}
        
        .category-card.production::before {{
            background: linear-gradient(90deg, #28a745, #20c997);
        }}
        
        .category-card.test::before {{
            background: linear-gradient(90deg, #ffc107, #fd7e14);
        }}
        
        .category-card.tooling::before {{
            background: linear-gradient(90deg, #17a2b8, #6f42c1);
        }}
        
        .category-card.scripts::before {{
            background: linear-gradient(90deg, #6c757d, #495057);
        }}
        
        .category-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        }}
        
        .category-title {{
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .category-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-size: 1.5em;
            font-weight: 700;
            color: #2c3e50;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .orphan-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .god-classes-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .god-classes-controls {{
            margin: 15px 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .god-class-item {{
            background: #fff0f5;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #e83e8c;
        }}
        
        .god-class-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .god-class-name {{
            font-weight: bold;
            color: #e83e8c;
        }}
        
        .god-class-methods {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .analyze-btn {{
            background: #e83e8c;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
        }}
        
        .analyze-btn:hover {{
            background: #d73a7b;
        }}
        
        .god-class-analysis {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            border: 1px solid #dee2e6;
        }}
        
        .refactor-plan {{
            margin-top: 15px;
        }}
        
        .plan-step {{
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            border-left: 3px solid #28a745;
        }}
        
        .orphan-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .orphan-item {{
            background: #fff3cd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
            transition: all 0.2s;
        }}
        
        .orphan-item:hover {{
            background: #fff8db;
            transform: translateX(3px);
        }}
        
        .orphan-header {{
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 5px;
        }}
        
        .orphan-name {{
            font-weight: 600;
            color: #856404;
        }}
        
        .confidence-badge {{
            background: #dc3545;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        
        .confidence-high {{
            background: #dc3545;
        }}
        
        .confidence-medium {{
            background: #ffc107;
            color: #000;
        }}
        
        .confidence-low {{
            background: #28a745;
        }}
        
        .orphan-meta {{
            font-size: 0.9em;
            color: #6c757d;
        }}
        
        .loading {{
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 20px;
        }}
        
        .error {{
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #c62828;
        }}
        
        .success {{
            background: #e8f5e8;
            color: #2e7d32;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #2e7d32;
        }}
        
        .hidden {{
            display: none;
        }}
        
        .chart-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #2c3e50;
            text-align: center;
            font-weight: 600;
        }}
        
        .chart-container {{
            position: relative;
            height: 300px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Dashboard Categorizado de Código</h1>
            <p class="subtitle">Análisis Inteligente por Directorio - Scrapper LLM</p>
            
            <div class="filter-tabs">
                <div class="tab active" data-category="all" onclick="filterByCategory('all')">
                    📊 Todo
                </div>
                <div class="tab production" data-category="production" onclick="filterByCategory('production')">
                    🏭 Producción (/src/)
                </div>
                <div class="tab test" data-category="test" onclick="filterByCategory('test')">
                    🧪 Tests
                </div>
                <div class="tab tooling" data-category="tooling" onclick="filterByCategory('tooling')">
                    🔧 Tools
                </div>
                <div class="tab scripts" data-category="scripts" onclick="filterByCategory('scripts')">
                    📜 Scripts
                </div>
                <div class="tab god-classes" data-category="god-classes" onclick="showGodClasses()">
                    🧠 God Classes
                </div>
            </div>
            
            <div class="controls">
                <button class="btn" onclick="refreshDashboard()">🔄 Actualizar</button>
                <button class="btn smart" onclick="runSmartAnalysis()" id="smartBtn">
                    🧠 Análisis Inteligente
                </button>
                <button class="btn" onclick="toggleRAGSection()">🤖 RAG Assistant</button>
            </div>
        </div>
        
        <div id="messages"></div>
        
        <!-- Sección RAG con filtros -->
        <div class="rag-section hidden" id="ragSection">
            <h3>🤖 Asistente de Código Categorizado</h3>
            <input type="text" class="rag-input" id="ragInput" 
                   placeholder="Pregunta sobre el código... Puedes filtrar: 'funciones en /src/', 'tests de integración', etc."
                   onkeypress="handleRAGEnter(event)">
            <button class="btn smart" onclick="askRAGQuestion()" style="margin-top: 10px;">
                🔍 Preguntar
            </button>
            <div class="filter-hint">
                💡 <strong>Tips de filtros:</strong> 
                "código de producción", "funciones en src/api", "tests huérfanos", "herramientas de refactoring"
            </div>
            <div id="ragResponse"></div>
        </div>
        
        <!-- Vista por categorías -->
        <div class="category-grid" id="categoryGrid">
            <div class="loading">Cargando análisis categorizado...</div>
        </div>
        
        <!-- Análisis de código huérfano inteligente -->
        <div class="orphan-section" id="orphanSection">
            <h3>🎯 Código Huérfano en Producción</h3>
            <p>Análisis inteligente enfocado en código de producción (/src/) con alta confianza</p>
            <div id="orphanContent">
                <div class="loading">Ejecuta "Análisis Inteligente" para ver código huérfano</div>
            </div>
        </div>
        
        <!-- Gráfico de distribución -->
        <div class="chart-section">
            <div class="chart-title">📊 Distribución por Categoría</div>
            <div class="chart-container">
                <canvas id="categoryChart"></canvas>
            </div>
        </div>
        
        <div class="god-classes-section hidden" id="godClassesSection">
            <h3>🧠 God Classes Detectadas</h3>
            <div class="god-classes-controls">
                <button class="btn" onclick="detectGodClasses()">🔍 Detectar God Classes</button>
                <span id="godClassesStatus">Haz clic para detectar God classes en el proyecto</span>
            </div>
            <div id="godClassesList"></div>
        </div>
        
        <div class="last-update" id="last-update"></div>
    </div>
    
    <script>
        const SMART_ENABLED = {smart_enabled};
        let currentCategory = 'all';
        let categoryChart = null;
        let smartAnalysisData = null;
        
        // Cargar datos inicial
        loadDashboard();
        
        function showMessage(message, type = 'success') {{
            const messagesDiv = document.getElementById('messages');
            const messageEl = document.createElement('div');
            messageEl.className = type;
            messageEl.textContent = message;
            messagesDiv.appendChild(messageEl);
            
            setTimeout(() => {{
                if (messagesDiv.contains(messageEl)) {{
                    messagesDiv.removeChild(messageEl);
                }}
            }}, 5000);
        }}
        
        async function loadDashboard() {{
            try {{
                await Promise.all([
                    loadCategoryBreakdown(),
                    loadCategoryChart()
                ]);
                showMessage('Dashboard categorizado cargado');
            }} catch (error) {{
                console.error('Error loading dashboard:', error);
                showMessage('Error cargando dashboard: ' + error.message, 'error');
            }}
        }}
        
        async function loadCategoryBreakdown() {{
            try {{
                const response = await fetch('/api/category-breakdown');
                if (!response.ok) throw new Error('Error cargando categorías');
                const data = await response.json();
                
                const categoryGrid = document.getElementById('categoryGrid');
                let html = '';
                
                // Generar tarjetas por categoría
                const categories = [
                    {{ key: 'production', name: 'Código de Producción', icon: '🏭', description: 'Código principal en /src/' }},
                    {{ key: 'test', name: 'Tests', icon: '🧪', description: 'Código de testing' }},
                    {{ key: 'tooling', name: 'Herramientas', icon: '🔧', description: 'Tools de desarrollo' }},
                    {{ key: 'scripts', name: 'Scripts', icon: '📜', description: 'Scripts de automatización' }}
                ];
                
                categories.forEach(category => {{
                    const categoryData = data[category.key] || {{ total: 0, functions: 0, classes: 0, avg_complexity: 0 }};
                    
                    html += `
                        <div class="category-card ${{category.key}}" data-category="${{category.key}}">
                            <div class="category-title">
                                ${{category.icon}} ${{category.name}}
                            </div>
                            <p style="color: #666; margin-bottom: 15px; font-size: 0.9em;">${{category.description}}</p>
                            <div class="category-stats">
                                <div class="stat-item">
                                    <div class="stat-value">${{categoryData.total || 0}}</div>
                                    <div class="stat-label">Total</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${{categoryData.functions || 0}}</div>
                                    <div class="stat-label">Funciones</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${{categoryData.classes || 0}}</div>
                                    <div class="stat-label">Clases</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${{(categoryData.avg_complexity || 0).toFixed(1)}}</div>
                                    <div class="stat-label">Complejidad</div>
                                </div>
                            </div>
                        </div>
                    `;
                }});
                
                categoryGrid.innerHTML = html;
                
            }} catch (error) {{
                document.getElementById('categoryGrid').innerHTML = 
                    `<div class="error">Error cargando categorías: ${{error.message}}</div>`;
            }}
        }}
        
        async function loadCategoryChart() {{
            try {{
                const response = await fetch('/api/category-breakdown');
                if (!response.ok) throw new Error('Error cargando datos del gráfico');
                const data = await response.json();
                
                const ctx = document.getElementById('categoryChart');
                
                if (categoryChart) {{
                    categoryChart.destroy();
                }}
                
                const labels = ['Producción', 'Tests', 'Tools', 'Scripts'];
                const values = [
                    data.production?.total || 0,
                    data.test?.total || 0,
                    data.tooling?.total || 0,
                    data.scripts?.total || 0
                ];
                const colors = ['#28a745', '#ffc107', '#17a2b8', '#6c757d'];
                
                categoryChart = new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            data: values,
                            backgroundColor: colors,
                            borderWidth: 2,
                            borderColor: '#fff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'bottom'
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((context.parsed / total) * 100).toFixed(1);
                                        return `${{context.label}}: ${{context.parsed}} (${{percentage}}%)`;
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
                
            }} catch (error) {{
                console.error('Error loading chart:', error);
            }}
        }}
        
        async function runSmartAnalysis() {{
            if (!SMART_ENABLED) {{
                showMessage('Análisis inteligente no disponible', 'error');
                return;
            }}
            
            const smartBtn = document.getElementById('smartBtn');
            smartBtn.textContent = '🧠 Analizando...';
            smartBtn.disabled = true;
            
            try {{
                const response = await fetch('/api/smart-analysis');
                if (!response.ok) throw new Error('Error en análisis inteligente');
                
                smartAnalysisData = await response.json();
                displaySmartAnalysis(smartAnalysisData);
                showMessage('Análisis inteligente completado');
                
            }} catch (error) {{
                showMessage('Error en análisis: ' + error.message, 'error');
            }} finally {{
                smartBtn.textContent = '🧠 Análisis Inteligente';
                smartBtn.disabled = false;
            }}
        }}
        
        function displaySmartAnalysis(data) {{
            if (!data.orphan_summary) return;
            
            const orphanContent = document.getElementById('orphanContent');
            const summary = data.orphan_summary;
            
            let html = `
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4>📊 Resumen de Código Huérfano en Producción</h4>
                    <p>📁 Total en /src/: <strong>${{summary.total_production_chunks}}</strong> componentes</p>
                    <p>❌ Huérfanos detectados: <strong>${{summary.production_orphans}}</strong> (${{(summary.orphan_rate || 0).toFixed(1)}}%)</p>
                    <p>🎯 Alta confianza: <strong>${{summary.high_confidence_orphans}}</strong> candidatos</p>
                </div>
            `;
            
            if (summary.top_orphan_candidates && summary.top_orphan_candidates.length > 0) {{
                html += '<div class="orphan-list">';
                
                summary.top_orphan_candidates.forEach((orphan, index) => {{
                    const confidence = orphan.confidence;
                    let confidenceClass = 'confidence-low';
                    let confidenceText = 'Baja';
                    
                    if (confidence > 0.8) {{
                        confidenceClass = 'confidence-high';
                        confidenceText = 'Alta';
                    }} else if (confidence > 0.6) {{
                        confidenceClass = 'confidence-medium';
                        confidenceText = 'Media';
                    }}
                    
                    html += `
                        <div class="orphan-item">
                            <div class="orphan-header">
                                <span class="orphan-name">${{orphan.name}}</span>
                                <span class="confidence-badge ${{confidenceClass}}">${{confidenceText}} (${{(confidence * 100).toFixed(0)}}%)</span>
                            </div>
                            <div class="orphan-meta">
                                📂 ${{orphan.file}} | 
                                🎯 Prioridad: ${{orphan.priority}}/10 | 
                                💼 Valor: ${{orphan.business_value}}/10 | 
                                📈 Complejidad: ${{orphan.complexity}}
                            </div>
                        </div>
                    `;
                }});
                
                html += '</div>';
            }} else {{
                html += '<p style="text-align: center; color: #28a745; font-weight: 500;">🎉 ¡No se detectó código huérfano con alta confianza en producción!</p>';
            }}
            
            orphanContent.innerHTML = html;
        }}
        
        function filterByCategory(category) {{
            currentCategory = category;
            
            // Actualizar tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
                if (tab.dataset.category === category) {{
                    tab.classList.add('active');
                }}
            }});
            
            // Filtrar contenido (placeholder - implementar según necesidad)
            showMessage(`Filtrando por: ${{category === 'all' ? 'Todo' : category}}`);
        }}
        
        function toggleRAGSection() {{
            const section = document.getElementById('ragSection');
            section.classList.toggle('hidden');
        }}
        
        function handleRAGEnter(event) {{
            if (event.key === 'Enter') {{
                askRAGQuestion();
            }}
        }}
        
        async function askRAGQuestion() {{
            const input = document.getElementById('ragInput');
            const question = input.value.trim();
            
            if (!question) {{
                showMessage('Por favor escribe una pregunta', 'error');
                return;
            }}
            
            const responseDiv = document.getElementById('ragResponse');
            responseDiv.innerHTML = '<div class="loading">🤖 Analizando código categorizado...</div>';
            
            try {{
                // Agregar contexto de categoría a la pregunta
                let contextualQuestion = question;
                if (currentCategory !== 'all') {{
                    contextualQuestion = `En el contexto de ${{currentCategory}}: ${{question}}`;
                }}
                
                const response = await fetch(`/api/ask-code?q=${{encodeURIComponent(contextualQuestion)}}`);
                if (!response.ok) throw new Error('Error en consulta RAG');
                
                const data = await response.json();
                
                let sourcesHtml = '';
                if (data.sources && data.sources.length > 0) {{
                    sourcesHtml = '<div style="margin-top: 15px;"><strong>📚 Fuentes encontradas:</strong>';
                    data.sources.slice(0, 3).forEach(source => {{
                        const categoryBadge = getCategoryBadge(source.file);
                        sourcesHtml += `
                            <div style="background: white; border-radius: 8px; padding: 10px; margin: 5px 0; border-left: 3px solid #4CAF50;">
                                <strong>${{source.name}}</strong> (${{source.type}}) ${{categoryBadge}}
                                <br>📂 ${{source.file}} (líneas ${{source.lines}})
                                <br>🎯 Relevancia: ${{(source.score * 100).toFixed(1)}}%
                            </div>
                        `;
                    }});
                    sourcesHtml += '</div>';
                }}
                
                responseDiv.innerHTML = `
                    <div style="background: #f8f9fa; border-radius: 15px; padding: 20px; margin-top: 15px; border-left: 4px solid #667eea;">
                        <strong>💬 Respuesta (${{currentCategory === 'all' ? 'Todo' : currentCategory}}):</strong>
                        <p style="margin: 10px 0;">${{data.answer}}</p>
                        ${{sourcesHtml}}
                        <div style="margin-top: 15px; font-size: 0.9em; color: #666;">
                            ⏱️ ${{data.response_time ? data.response_time.toFixed(2) : 'N/A'}}s • 
                            🎯 Confianza: ${{(data.confidence * 100).toFixed(1)}}%
                        </div>
                    </div>
                `;
                
            }} catch (error) {{
                responseDiv.innerHTML = `<div class="error">❌ Error: ${{error.message}}</div>`;
            }}
        }}
        
        function getCategoryBadge(filePath) {{
            if (filePath.includes('src/')) {{
                return '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.7em;">PROD</span>';
            }} else if (filePath.includes('test')) {{
                return '<span style="background: #ffc107; color: black; padding: 2px 6px; border-radius: 10px; font-size: 0.7em;">TEST</span>';
            }} else if (filePath.includes('tool')) {{
                return '<span style="background: #17a2b8; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.7em;">TOOL</span>';
            }} else if (filePath.includes('script')) {{
                return '<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.7em;">SCRIPT</span>';
            }}
            return '';
        }}
        
        async function refreshDashboard() {{
            showMessage('Actualizando dashboard...');
            await loadDashboard();
        }}
        
        // God Classes Functions
        function showGodClasses() {{
            // Hide other sections
            document.getElementById('categoryGrid').style.display = 'none';
            document.getElementById('orphanSection').style.display = 'none';
            document.getElementById('ragSection').classList.add('hidden');
            
            // Show God Classes section
            document.getElementById('godClassesSection').classList.remove('hidden');
            
            // Update tab states
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelector('.tab[data-category="god-classes"]').classList.add('active');
        }}
        
        async function detectGodClasses() {{
            const statusSpan = document.getElementById('godClassesStatus');
            const listDiv = document.getElementById('godClassesList');
            
            statusSpan.textContent = '🔍 Detectando God classes...';
            listDiv.innerHTML = '';
            
            try {{
                const response = await fetch('/api/god-classes');
                const data = await response.json();
                
                if (data.error) {{
                    statusSpan.textContent = '❌ Error: ' + data.error;
                    return;
                }}
                
                statusSpan.textContent = `✅ Detectadas ${{data.total_detected}} God classes`;
                
                if (data.god_classes.length === 0) {{
                    listDiv.innerHTML = '<div style="text-align: center; color: #28a745; padding: 20px;">🎉 ¡No se encontraron God classes! Tu código está bien estructurado.</div>';
                    return;
                }}
                
                listDiv.innerHTML = data.god_classes.map(godClass => `
                    <div class="god-class-item">
                        <div class="god-class-header">
                            <div>
                                <div class="god-class-name">${{godClass.class_name}}</div>
                                <div class="god-class-methods">${{godClass.method_count}} métodos en ${{godClass.file}}</div>
                            </div>
                            <button class="analyze-btn" onclick="analyzeGodClass('${{godClass.file}}', '${{godClass.class_name}}')">
                                🧠 Analizar con IA
                            </button>
                        </div>
                        <div id="analysis-${{godClass.file.replace(/[^a-zA-Z0-9]/g, '_')}}"></div>
                    </div>
                `).join('');
                
            }} catch (error) {{
                statusSpan.textContent = '❌ Error detectando God classes: ' + error.message;
            }}
        }}
        
        async function analyzeGodClass(filePath, className) {{
            const analysisId = filePath.replace(/[^a-zA-Z0-9]/g, '_');
            const analysisDiv = document.getElementById('analysis-' + analysisId);
            
            analysisDiv.innerHTML = '<div style="color: #667eea; padding: 10px;">🧠 Analizando con IA local... Esto puede tomar 15-30 segundos.</div>';
            
            try {{
                const response = await fetch(`/api/analyze-god-class?file=${{encodeURIComponent(filePath)}}`);
                const data = await response.json();
                
                if (data.error) {{
                    analysisDiv.innerHTML = `<div style="color: #dc3545; padding: 10px;">❌ Error: ${{data.error}}</div>`;
                    return;
                }}
                
                const summary = data.summary;
                const plan = data.refactor_plan || [];
                
                analysisDiv.innerHTML = `
                    <div class="god-class-analysis">
                        <h4>📊 Análisis de ${{data.class_name}}</h4>
                        <div style="margin: 10px 0;">
                            <strong>💡 Insights clave:</strong>
                            <ul style="margin: 5px 0 0 20px;">
                                ${{summary.key_insights ? summary.key_insights.map(insight => `<li>${{insight}}</li>`).join('') : '<li>Análisis disponible</li>'}}
                            </ul>
                        </div>
                        
                        <div style="margin: 15px 0;">
                            <strong>🎯 Refactorabilidad:</strong> ${{summary.refactorability || 'Media'}}
                        </div>
                        
                        ${{plan.length > 0 ? `
                            <div class="refactor-plan">
                                <strong>🛣️ Plan de Refactorización:</strong>
                                ${{plan.slice(0, 4).map(step => `
                                    <div class="plan-step">
                                        <strong>Paso ${{step.step}}:</strong> ${{step.action}}
                                        <br><small>⏱️ ${{step.time_estimate || 'N/A'}} • 🚦 Riesgo: ${{step.risk}}</small>
                                    </div>
                                `).join('')}}
                            </div>
                        ` : ''}}
                        
                        <div style="margin-top: 15px; font-size: 0.9em; color: #666;">
                            ⏱️ Análisis completado en ${{data.performance ? data.performance.analysis_time.toFixed(1) : 'N/A'}}s
                        </div>
                    </div>
                `;
                
            }} catch (error) {{
                analysisDiv.innerHTML = `<div style="color: #dc3545; padding: 10px;">❌ Error analizando: ${{error.message}}</div>`;
            }}
        }}
    </script>
</body>
</html>'''
        
        self.send_html_response(html_content)
    
    def handle_god_class_detection(self) -> tuple[int, str, str]:
        """Detectar God classes en el proyecto."""
        try:
            god_classes = []
            
            # Buscar archivos Python
            for python_file in self.data_provider.project_root.rglob("*.py"):
                if python_file.is_file():
                    try:
                        with open(python_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        tree = ast.parse(content)
                        
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                # Contar métodos
                                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                                if len(methods) >= 10:  # Umbral para God class
                                    god_classes.append({
                                        'class_name': node.name,
                                        'method_count': len(methods),
                                        'file': str(python_file.relative_to(self.data_provider.project_root))
                                    })
                    except Exception as e:
                        print(f"Error analizando {python_file}: {e}")
                        continue
            
            result = {
                'total_detected': len(god_classes),
                'god_classes': god_classes
            }
            
            return 200, 'application/json', json.dumps(result)
            
        except Exception as e:
            return 500, 'application/json', json.dumps({'error': f'Error en detección: {e}'})
    
    def handle_god_class_analysis(self, file_path: str) -> tuple[int, str, str]:
        """Analizar God class específica con IA."""
        try:
            if not self.data_provider.god_class_refactor:
                return 500, 'application/json', json.dumps({'error': 'God Class Refactor no disponible'})
            
            # Convertir ruta relativa a absoluta
            full_path = self.data_provider.project_root / file_path
            
            # Analizar con IA
            analysis = self.data_provider.god_class_refactor.analyze_god_class(str(full_path))
            
            return 200, 'application/json', json.dumps(analysis)
            
        except Exception as e:
            return 500, 'application/json', json.dumps({'error': f'Error en análisis: {e}'})
    
    def serve_summary(self):
        """Servir resumen general."""
        try:
            data = self.load_metrics()
            project_metrics = data.get('project_metrics', {})
            
            summary = {
                'total_files': project_metrics.get('total_files', 0),
                'total_functions': project_metrics.get('total_functions', 0),
                'total_lines': project_metrics.get('total_lines', 0),
                'orphan_functions': project_metrics.get('orphan_functions', 0),
                'maintainability_score': project_metrics.get('maintainability_score', 0),
                'complexity_average': project_metrics.get('complexity_average', 0),
                'last_update': data.get('timestamp', '')
            }
            
            self.send_json_response(summary)
        except Exception as e:
            self.send_error(500, f"Error cargando resumen: {str(e)}")
    
    def serve_smart_analysis(self):
        """Servir análisis inteligente."""
        if not HAS_SMART_ANALYSIS:
            self.send_json_response({
                'error': 'Análisis inteligente no disponible'
            })
            return
        
        try:
            if not self.smart_analyzer:
                self.send_json_response({
                    'error': 'Analizador inteligente no disponible'
                })
                return
            
            # Ejecutar análisis
            categorized = self.smart_analyzer.analyze_project()
            orphan_summary = self.smart_analyzer.get_orphan_summary()
            
            result = {
                'categorized': {k: len(v) for k, v in categorized.items()},
                'orphan_summary': orphan_summary,
                'timestamp': time.time()
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({
                'error': f'Error en análisis inteligente: {str(e)}'
            })
    
    def serve_category_breakdown(self):
        """Servir desglose por categoría."""
        try:
            # Usar el data provider para cargar métricas
            if not self.data_provider.metrics_file.exists():
                self.send_json_response({
                    'error': 'Archivo de métricas no encontrado'
                })
                return
            
            with open(self.data_provider.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_metrics = data.get('file_metrics', {})
            
            # Categorizar archivos por path
            categories = {
                'production': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []},
                'test': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []},
                'tooling': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []},
                'scripts': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []}
            }
            
            for file_path, metrics in file_metrics.items():
                path_lower = file_path.lower()
                
                if 'src/' in path_lower:
                    category = 'production'
                elif 'test' in path_lower:
                    category = 'test'
                elif 'tool' in path_lower:
                    category = 'tooling'
                elif 'script' in path_lower:
                    category = 'scripts'
                else:
                    continue
                
                categories[category]['total'] += 1
                categories[category]['functions'] += metrics['functions_count']
                categories[category]['complexity'].append(metrics['complexity_score'])
            
            # Calcular promedios
            for category in categories:
                complexities = categories[category]['complexity']
                categories[category]['avg_complexity'] = sum(complexities) / len(complexities) if complexities else 0
                del categories[category]['complexity']  # No enviar array completo
            
            self.send_json_response(categories)
            
        except Exception as e:
            self.send_json_response({
                'error': f'Error cargando categorías: {str(e)}'
            })
    
    def serve_orphan_analysis(self):
        """Servir análisis de código huérfano."""
        # Placeholder - usar métricas existentes
        self.send_json_response({
            'placeholder': 'Análisis de huérfanos pendiente de implementación'
        })
    
    def serve_code_question(self, query_params: Dict):
        """Servir respuesta a pregunta sobre código."""
        question = query_params.get('q', [''])[0]
        if not question:
            self.send_error(400, "Parámetro 'q' requerido")
            return
        
        try:
            if not self.rag_system:
                self.send_json_response({
                    'error': 'Sistema RAG no disponible',
                    'answer': 'Sistema RAG no inicializado'
                })
                return
            
            question = unquote(question)
            
            start_time = time.time()
            result = self.rag_system.ask_question(question)
            response_time = time.time() - start_time
            
            result['response_time'] = response_time
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({
                'error': str(e),
                'answer': f'Error procesando pregunta: {str(e)}'
            })
    
    def serve_filtered_code(self, query_params: Dict):
        """Servir código filtrado por categoría."""
        category = query_params.get('category', ['all'])[0]
        
        try:
            # Placeholder para filtrado
            result = {
                'category': category,
                'items': [],
                'total': 0
            }
            
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({
                'error': f'Error filtrando código: {str(e)}'
            })
    
    
    def log_message(self, format, *args):
        """Suprimir logs del servidor."""
        pass

def find_free_port(start_port=8090):
    """Encontrar puerto libre."""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def main():
    """Ejecutar servidor categorizado."""
    project_root = Path(__file__).parent.parent
    metrics_file = project_root / "CODE_METRICS_REPORT.json"
    
    if not metrics_file.exists():
        print("❌ Archivo de métricas no encontrado.")
        print("💡 Ejecutar: make analyze-metrics")
        return 1
    
    port = find_free_port(8090)
    if not port:
        print("❌ No se pudo encontrar un puerto libre")
        return 1
    
    print("🎯 INICIANDO DASHBOARD CATEGORIZADO")
    print("=" * 50)
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"🧠 Análisis inteligente: {'✅ Disponible' if HAS_SMART_ANALYSIS else '❌ No disponible'}")
    print(f"📂 Métricas: {metrics_file}")
    
    if not HAS_SMART_ANALYSIS:
        print("💡 Para análisis inteligente: verificar dependencias")
    
    print("\n🌐 Abriendo navegador...")
    
    server = HTTPServer(('localhost', port), CategorizedDashboardHandler)
    
    def open_browser():
        time.sleep(1)
        try:
            webbrowser.open(f'http://localhost:{port}')
        except:
            pass
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor cerrado")
        server.shutdown()
        return 0
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())