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
            self.send_html_response(html_content)

        except FileNotFoundError:
            self.send_error(404, "Dashboard HTML no encontrado")
            return
        
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
        """Servir desglose por categoría (ACTUALIZADO para la estructura del proyecto)."""
        try:
            if not self.data_provider.metrics_file.exists():
                self.send_json_response({'error': 'Archivo de métricas no encontrado'})
                return
            
            with open(self.data_provider.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            file_metrics = data.get('file_metrics', {})
            
            categories = {
                'production': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []},
                'test': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []},
                'tooling': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []},
                'scripts': {'total': 0, 'functions': 0, 'classes': 0, 'complexity': []}
            }
            
            # ✅ Lógica de categorización ajustada a tu 'tree'
            for file_path, metrics in file_metrics.items():
                path_lower = file_path.lower()
                category = None
                
                # 1. Código de Producción (ahora incluye src y refactored_assetplan)
                if path_lower.startswith('src/') or path_lower.startswith('refactored_assetplan/'):
                    category = 'production'
                
                # 2. Scripts (ahora incluye la carpeta 'scripts' y archivos .py en la raíz)
                elif path_lower.startswith('scripts/') or (not '/' in path_lower and path_lower.endswith('.py')):
                    category = 'scripts'
                
                # 3. Directorio de Tests (se mantiene por si lo agregas en el futuro)
                elif path_lower.startswith('tests/'):
                    category = 'test'

                # 4. Herramientas (se mantiene por si lo agregas en el futuro)
                elif path_lower.startswith('tools/'):
                    category = 'tooling'

                # Si se encontró una categoría, agregar las métricas
                if category:
                    categories[category]['total'] += 1
                    categories[category]['functions'] += metrics.get('functions_count', 0)
                    categories[category]['classes'] += metrics.get('classes_count', 0)
                    categories[category]['complexity'].append(metrics.get('complexity_score', 0))
            
            # Calcular los promedios de complejidad
            for cat_name, cat_data in categories.items():
                complexities = cat_data['complexity']
                cat_data['avg_complexity'] = round(sum(complexities) / len(complexities) if complexities else 0, 1)
                del cat_data['complexity']
            
            self.send_json_response(categories)
            
        except Exception as e:
            self.send_json_response({'error': f'Error cargando categorías: {str(e)}'})
    
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