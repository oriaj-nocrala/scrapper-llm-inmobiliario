"""
AssetPlan.cl extractor actualizado según GUIA_UNICA_RESUMEN.md
Implementa el flujo exacto de navegación y extracción documentado.
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..infrastructure.human_behavior import HumanBehaviorSimulator
from ..models import Property, PropertyCollection, PropertyTypology
from .debug_manager import DebugManager
from .navigation_manager import NavigationManager
from .data_parser import DataParser

logger = logging.getLogger(__name__)


class AssetPlanExtractorV2:
    """
    Extractor para AssetPlan.cl siguiendo GUIA_UNICA_RESUMEN.md (refactorizado)
    Implementa el flujo completo: busqueda -> edificios -> tipologias -> departamentos
    """
    
    def __init__(self, driver: WebDriver, base_url: str = "https://www.assetplan.cl", debug_mode=False):
        """Initialize the AssetPlan extractor.
        
        Args:
            driver: WebDriver instance
            base_url: Base URL for AssetPlan
        """
        self.driver = driver
        self.base_url = base_url
        self.behavior = HumanBehaviorSimulator(driver)
        self.debug_mode = debug_mode
        
        # URL correcta según la guía
        self.search_url = f"{base_url}/arriendo/departamento"
        
        # Initialize specialized components
        self.debug_manager = DebugManager(driver)
        self.navigation_manager = NavigationManager(driver, self.debug_manager)
        self.data_parser = DataParser()
        
        # Behavior configuration
        self.human_like_behavior = False  # Default: no human simulation
        self.behavior_mode = "extreme"    # Default: extreme mode
        self.extreme_mode = True          # Default: extreme mode enabled
        
        # Click control para prevenir clicks múltiples
        self._click_in_progress = False
        self._last_clicked_url = None
        self._click_count = 0
        self._click_start_time = None
        
        # Legacy properties for backward compatibility
        self.wait = self.navigation_manager.wait
        self.fast_wait = self.navigation_manager.fast_wait
    
    def enable_debug_mode(self, enabled: bool = True):
        """Enable or disable debug mode with visual indicators."""
        self.debug_mode = enabled
        self.debug_manager.enable_debug_mode(enabled)
    
    def configure_behavior_mode(self, human_like: bool = False, behavior_mode: str = "extreme"):
        """Configure scraper behavior mode."""
        self.human_like_behavior = human_like
        self.behavior_mode = behavior_mode
        self.extreme_mode = (behavior_mode == "extreme")
        
        # Configure navigation manager
        self.navigation_manager.configure_behavior_mode(human_like, behavior_mode)
        
        # Update legacy properties
        self.wait = self.navigation_manager.wait
        self.fast_wait = self.navigation_manager.fast_wait
    
    # Delegate methods to specialized components
    def _highlight_element(self, element, highlight_type="highlight", duration=1.5):
        """Delegate to debug manager."""
        return self.debug_manager.highlight_element(element, highlight_type, duration)
    
    def _show_debug_info(self, message: str, duration: float = 3.0):
        """Delegate to debug manager."""
        return self.debug_manager.show_debug_info(message, duration)
    
    def _debug_click(self, element, context: str = ""):
        """Delegate to debug manager."""
        return self.debug_manager.debug_click(element, context)
    
    # Navigation delegate methods
    def _smart_delay(self, min_delay: float, max_delay: float):
        """Delegate to navigation manager."""
        return self.navigation_manager.smart_delay(min_delay, max_delay)
    
    def _wait_for_complete_navigation(self, initial_url: str, timeout: float = 8.0) -> bool:
        """Delegate to navigation manager."""
        return self.navigation_manager.wait_for_complete_navigation(initial_url, timeout)
    
    def _smart_back_to_modal(self):
        """Delegate to navigation manager."""
        return self.navigation_manager.smart_back_to_modal()
    
    def _find_element_robust(self, selectors: list, parent=None):
        """Delegate to navigation manager."""
        return self.navigation_manager.find_element_robust(selectors, parent)
    
    def _find_elements_robust(self, selectors: list, parent=None):
        """Delegate to navigation manager."""
        return self.navigation_manager.find_elements_robust(selectors, parent)
    
    # Data parsing delegate methods
    def _parse_price_uf(self, price_text: str):
        """Delegate to data parser."""
        return self.data_parser.parse_price_uf(price_text)
    
    def _parse_area(self, area_text: str):
        """Delegate to data parser."""
        return self.data_parser.parse_area(area_text)
    
    def _parse_bedrooms(self, bedrooms_text: str):
        """Delegate to data parser."""
        return self.data_parser.parse_bedrooms(bedrooms_text)
    
    def _parse_bathrooms(self, bathrooms_text: str):
        """Delegate to data parser."""
        return self.data_parser.parse_bathrooms(bathrooms_text)
    
    def _extract_floor_from_unit_number(self, unit_number: str):
        """Delegate to data parser."""
        return self.data_parser.extract_floor_from_unit_number(unit_number)
    
    def _extract_property_id_from_url(self, url: str):
        """Delegate to data parser."""
        return self.data_parser.extract_property_id_from_url(url)
    
    def _generate_typology_id(self, bedrooms, bathrooms, area_m2):
        """Delegate to data parser."""
        return self.data_parser.generate_typology_id(bedrooms, bathrooms, area_m2)
    
    def _is_valid_department_url(self, url: str):
        """Delegate to data parser."""
        return self.data_parser.is_valid_department_url(url)
    
    def _validate_building_data(self, building_data):
        """Delegate to data parser."""
        return self.data_parser.validate_building_data(building_data)
    
    def _monitor_navigation(self, context: str = "", timeout: float = 10.0):
        """Monitor navigation changes with concise logging."""
        if not self.debug_mode:
            return
            
        try:
            current_url = self.driver.current_url
            
            # Log URL change only
            if current_url != self.last_url:
                logger.info(f"🔄 [{context}] {current_url}")
                self._show_debug_info(f"Navegando: {context}")
                self.last_url = current_url
            
            # Check for critical errors only
            try:
                critical_errors = ["500", "internal server error", "connection refused", "timeout"]
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                for indicator in critical_errors:
                    if indicator in page_text:
                        logger.warning(f"❌ [{context}] ERROR: {indicator}")
                        self._show_debug_info(f"ERROR: {indicator}")
                        break
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error navegación: {e}")
    
    def configure_behavior_mode(self, human_like: bool = False, behavior_mode: str = "extreme"):
        """Configure behavior mode. Default is extreme speed; human-like is optional."""
        self.human_like_behavior = human_like
        self.behavior_mode = behavior_mode
        self.extreme_mode = (behavior_mode == "extreme")
        
        # Configure waits based on mode
        if self.extreme_mode:
            self.fast_wait = WebDriverWait(self.driver, 2)  # Fast timeout for extreme mode
            if human_like:
                logger.info("⚡ MODO EXTREMO con simulación humana activada")
            else:
                logger.info("⚡ MODO EXTREMO: máxima velocidad (por defecto)")
        elif human_like:
            logger.info("🤖 Modo conservador con comportamiento humano")
        else:
            logger.info("🚀 Modo rápido estándar")
    
    def _get_wait(self):
        """Get appropriate WebDriverWait based on mode."""
        return self.fast_wait if self.extreme_mode and self.fast_wait else self.wait
    
    def _smart_delay(self, min_delay: float, max_delay: float):
        """Smart delay that respects extreme mode and human-like behavior settings."""
        if self.extreme_mode:
            # No delay in extreme mode
            return
        elif self.human_like_behavior:
            # Full human-like delay
            self.behavior.random_delay(min_delay, max_delay)
        else:
            # Minimal delay for stability
            import time
            time.sleep(min(0.1, min_delay))
    
    
    def _wait_for_complete_navigation(self, initial_url: str, timeout: float = 8.0) -> bool:
        """
        Espera navegación COMPLETA antes de continuar al siguiente item del modal.
        
        PREVIENE: múltiples cambios de radiobutton antes de que la navegación termine.
        
        Args:
            initial_url: URL antes del click
            timeout: Tiempo máximo de espera
            
        Returns:
            True si navegación se completó correctamente
        """
        import time
        start_time = time.time()
        
        # Fase 1: Esperar que cambie la URL (inicio de navegación)
        url_changed = False
        phase1_timeout = timeout * 0.4  # 40% del tiempo para cambio de URL
        
        logger.debug("🔄 [Nav] Fase 1: Esperando cambio de URL...")
        while time.time() - start_time < phase1_timeout:
            current_url = self.driver.current_url
            if current_url != initial_url:
                url_changed = True
                logger.debug(f"✅ [Nav] URL cambió: {current_url}")
                break
            time.sleep(0.05 if self.extreme_mode else 0.1)
        
        if not url_changed:
            logger.warning("❌ [Nav] Fase 1 FALLÓ: URL no cambió")
            return False
        
        # Fase 2: Esperar que aparezca selectedUnit (navegación específica)
        selected_unit_found = False
        phase2_timeout = timeout * 0.3  # 30% del tiempo para selectedUnit
        phase2_start = time.time()
        
        logger.debug("🔄 [Nav] Fase 2: Esperando selectedUnit en URL...")
        while time.time() - phase2_start < phase2_timeout:
            current_url = self.driver.current_url
            if "selectedUnit=" in current_url:
                selected_unit_found = True
                logger.debug("✅ [Nav] selectedUnit encontrado")
                break
            time.sleep(0.05 if self.extreme_mode else 0.1)
        
        if not selected_unit_found:
            logger.warning("❌ [Nav] Fase 2 FALLÓ: selectedUnit no encontrado")
            return False
        
        # Fase 3: Esperar que la página se cargue completamente (DOM estable)
        phase3_timeout = timeout * 0.3  # 30% del tiempo para carga completa
        phase3_start = time.time()
        
        logger.debug("🔄 [Nav] Fase 3: Esperando carga completa de página...")
        stable_count = 0
        required_stable = 3 if self.extreme_mode else 5  # checks consecutivos estables
        
        while time.time() - phase3_start < phase3_timeout:
            try:
                # Verificar elementos críticos de la página de departamento
                readystate = self.driver.execute_script("return document.readyState")
                has_content = len(self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, .property-detail, [data-testid], .grid")) > 0
                
                if readystate == "complete" and has_content:
                    stable_count += 1
                    if stable_count >= required_stable:
                        logger.debug("✅ [Nav] Fase 3: Página completamente cargada")
                        break
                else:
                    stable_count = 0
                    
            except Exception:
                stable_count = 0
            
            time.sleep(0.1 if self.extreme_mode else 0.2)
        
        # Verificación final: todo debe estar correcto
        final_url = self.driver.current_url
        navigation_complete = (
            final_url != initial_url and 
            "selectedUnit=" in final_url and 
            stable_count >= required_stable
        )
        
        if navigation_complete:
            elapsed = time.time() - start_time
            logger.info(f"✅ [Nav] COMPLETA en {elapsed:.2f}s: {final_url}")
            # CRÍTICO: Reset click state después de navegación exitosa
            self._reset_click_state()
        else:
            logger.warning(f"❌ [Nav] INCOMPLETA: stable={stable_count}, url={final_url}")
            # Reset click state también en caso de fallo para evitar deadlock
            self._reset_click_state()
        
        return navigation_complete
    
    def _smart_back_to_modal(self):
        """Smart navigation back to modal - construye URL correcta del modal."""
        try:
            current_url = self.driver.current_url
            logger.debug(f"🔙 URL actual antes del back: {current_url}")
            
            if "selectedUnit=" in current_url:
                # Construir URL del modal correctamente
                if "showUnits=true" in current_url:
                    # Ya tiene showUnits=true, solo remover selectedUnit
                    modal_url = current_url.split('&selectedUnit=')[0].split('?selectedUnit=')[0]
                else:
                    # Remover selectedUnit y agregar showUnits=true
                    base_url = current_url.split('&selectedUnit=')[0].split('?selectedUnit=')[0]
                    
                    if '?' in base_url:
                        modal_url = f"{base_url}&showUnits=true"
                    else:
                        modal_url = f"{base_url}?showUnits=true"
                
                logger.debug(f"🎯 Navegando a modal URL: {modal_url}")
                self.driver.get(modal_url)
                
                # Verificar que llegamos al modal
                try:
                    if self.extreme_mode:
                        # Polling rápido en modo extremo
                        import time
                        start_time = time.time()
                        while time.time() - start_time < 1.0:
                            if self.driver.find_elements(By.CSS_SELECTOR, "ul.divide-y.divide-gray-200"):
                                logger.debug("✅ Modal detectado")
                                return
                            time.sleep(0.05)
                        logger.warning("⚠️ Modal no detectado en modo extremo")
                    else:
                        # Wait normal
                        self._get_wait().until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.divide-y.divide-gray-200"))
                        )
                        logger.debug("✅ Modal detectado")
                except TimeoutException:
                    logger.error(f"❌ Modal no encontrado en URL: {modal_url}")
            else:
                logger.warning("⚠️ URL actual no contiene selectedUnit, no se puede construir modal URL")
                
        except Exception as e:
            logger.error(f"💥 Error en _smart_back_to_modal: {e}")
    
    def _wait_for_element_quick(self, selector: str, timeout: float = 1.0):
        """Quick element wait for extreme mode."""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.driver.find_element(By.CSS_SELECTOR, selector)
                return True
            except:
                time.sleep(0.05)  # 50ms polling
        return False
    
    def _debug_click(self, element, context: str = ""):
        """
        Perform click with ANTI-MULTIPLE-CLICK protection.
        
        PREVIENE: múltiples clicks antes de que la URL cambie.
        """
        import time
        current_url = self.driver.current_url
        
        # CONTROL CRÍTICO: Reset automático si URL cambió (significa que el click anterior funcionó)
        if self._last_clicked_url and current_url != self._last_clicked_url:
            logger.debug(f"🔄 [{context}] URL cambió desde último click, reseteando estado")
            self._click_in_progress = False
            self._last_clicked_url = current_url
            self._click_count = 0
            self._click_start_time = None
        
        # CONTROL CRÍTICO: Reset por timeout (si click no funcionó después de 3 segundos)
        if self._click_in_progress and self._click_start_time:
            elapsed = time.time() - self._click_start_time
            if elapsed > 3.0:  # 3 segundos timeout
                logger.warning(f"🕐 [{context}] TIMEOUT click anterior ({elapsed:.1f}s), reseteando estado")
                self._click_in_progress = False
                self._click_start_time = None
                self._click_count = 0
        
        # CONTROL CRÍTICO: Solo permitir UN click hasta cambio de URL o timeout
        if self._click_in_progress:
            logger.warning(f"🚫 [{context}] CLICK BLOQUEADO: esperando cambio de URL")
            return
        
        # Registrar el click
        self._click_in_progress = True
        self._last_clicked_url = current_url
        self._click_count += 1
        self._click_start_time = time.time()
        
        logger.debug(f"🖱️ [{context}] CLICK #{self._click_count} iniciado en: {current_url}")
        
        # Visual feedback en debug mode
        if self.debug_mode and not self.extreme_mode:
            self._highlight_element(element, "target", duration=0.5)
            logger.info(f"📌 [{context}] CLICK preparado")
            self._show_debug_info(f"CLICK: {context}")
        
        # Ejecutar el click
        try:
            element.click()
            logger.debug(f"✅ [{context}] CLICK ejecutado")
            
            if self.debug_mode and not self.extreme_mode:
                self._highlight_element(element, "clicked", duration=1.0)
                logger.info(f"✅ [{context}] CLICK ejecutado")
                
        except Exception as e:
            logger.error(f"❌ [{context}] CLICK falló: {e}")
            # Reset en caso de error
            self._click_in_progress = False
            self._click_start_time = None
            raise
    
    def _reset_click_state(self):
        """Reset click state para permitir siguiente click."""
        if self._click_in_progress:
            logger.debug(f"🔓 Click state reseteado después de {self._click_count} clicks")
        self._click_in_progress = False
        self._last_clicked_url = self.driver.current_url
        self._click_count = 0
        self._click_start_time = None
    
    def _wait_for_navigation_with_debug(self, expected_url_pattern: str = None, timeout: float = 10.0, context: str = ""):
        """Wait for navigation with mode-aware behavior."""
        import time
        start_time = time.time()
        
        # In extreme mode, reduce timeout and polling frequency
        if self.extreme_mode:
            timeout = min(timeout, 3.0)  # Max 3 seconds in extreme mode
            poll_interval = 0.1  # Check every 100ms
        else:
            poll_interval = 1.0 if not self.debug_mode else 1.0
        
        if self.debug_mode and not self.extreme_mode:
            logger.info(f"⏳ [{context}] Esperando navegación...")
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                
                # Monitor based on mode
                if not self.extreme_mode and self.debug_mode:
                    # Check URL every 2 seconds (less verbose)
                    if time.time() - start_time % 2 < 0.1:
                        self._monitor_navigation(context)
                
                # Check if we reached expected URL
                if expected_url_pattern and expected_url_pattern in current_url:
                    if not self.extreme_mode:
                        logger.info(f"✅ [{context}] Navegación exitosa")
                    return True
                
                time.sleep(poll_interval)
                
            except Exception as e:
                if not self.extreme_mode:
                    logger.error(f"Error navegación: {e}")
                break
        
        # Timeout reached
        if not self.extreme_mode:
            logger.warning(f"⏰ [{context}] TIMEOUT tras {timeout}s")
            if self.debug_mode:
                self._show_debug_info(f"TIMEOUT: {context}")
        return False
    
    def _find_element_robust(self, selectors: List[str], parent=None) -> Optional[WebElement]:
        """
        Busca un elemento usando múltiples selectores de fallback.
        
        Args:
            selectors: Lista de selectores CSS a probar en orden
            parent: Elemento padre donde buscar (opcional)
            
        Returns:
            WebElement encontrado o None
        """
        search_context = parent if parent else self.driver
        
        for selector in selectors:
            try:
                element = search_context.find_element(By.CSS_SELECTOR, selector)
                if element:
                    return element
            except NoSuchElementException:
                continue
        
        return None
    
    def _find_elements_robust(self, selectors: List[str], parent=None) -> List[WebElement]:
        """
        Busca elementos usando múltiples selectores de fallback.
        
        Args:
            selectors: Lista de selectores CSS a probar en orden
            parent: Elemento padre donde buscar (opcional)
            
        Returns:
            Lista de WebElements encontrados
        """
        search_context = parent if parent else self.driver
        
        for selector in selectors:
            try:
                elements = search_context.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except NoSuchElementException:
                continue
        
        return []
    
    def start_scraping(self, max_properties: int = 50, max_typologies: Optional[int] = None) -> PropertyCollection:
        """
        Inicia el proceso completo de scraping siguiendo la guía.
        
        Args:
            max_properties: Máximo número de propiedades a extraer
            max_typologies: Máximo número de tipologías/edificios a procesar (None = sin límite)
            
        Returns:
            Lista de propiedades extraídas
        """
        if not self.extreme_mode:
            typologies_info = f", max tipologías: {max_typologies}" if max_typologies else ""
            logger.info(f"🚀 Iniciando scraping AssetPlan.cl (max: {max_properties}{typologies_info})")
        else:
            logger.info(f"⚡ EXTREMO: {max_properties} props{f', {max_typologies} tipologías' if max_typologies else ''}")
        
        # Paso 1: Navegar a la página de búsqueda
        self._navigate_to_search_page()
        
        # Paso 2: Extraer lista de edificios (tarjetas de edificio)
        building_cards = self._extract_building_cards()
        if not self.extreme_mode:
            logger.info(f"🏢 {len(building_cards)} edificios encontrados")
        else:
            logger.info(f"⚡ {len(building_cards)} edificios")
        
        if not building_cards:
            logger.warning("No se encontraron edificios, intentando método alternativo")
            return self._extract_properties_alternative_method(max_properties)
        
        # Paso 3: Procesar edificios para obtener departamentos
        if max_typologies and max_typologies > 1:
            # Modo MULTI-TIPOLOGÍA: extraer de múltiples edificios
            properties = self._extract_from_multiple_buildings(
                building_cards, max_properties, max_typologies
            )
            processed_buildings = min(len(building_cards), max_typologies)
        else:
            # Modo ESTÁNDAR: procesar edificios secuencialmente
            properties = []
            processed_buildings = 0
            
            for building_data in building_cards:
                if len(properties) >= max_properties:
                    break
                    
                try:
                    # Validar datos del edificio antes de procesarlo
                    if not self._validate_building_data(building_data):
                        logger.debug(f"Edificio {building_data.get('name', 'unknown')} no pasó validación")
                        continue
                    
                    building_properties = self._process_building(building_data, max_properties - len(properties))
                    properties.extend(building_properties)
                    processed_buildings += 1
                    
                    if not self.extreme_mode:
                        logger.info(f"🏠 Edificio {processed_buildings}: +{len(building_properties)} (Total: {len(properties)})")
                    elif processed_buildings % 5 == 0:  # Log every 5th building in extreme mode
                        logger.info(f"⚡ {processed_buildings}: {len(properties)} total")
                    
                    # Delay entre edificios
                    self._smart_delay(1.0, 2.5)
                    
                except Exception as e:
                    # Usar manejo inteligente de errores
                    if self._handle_navigation_errors(e, f"procesando edificio {building_data.get('name', 'unknown')}"):
                        continue
                    else:
                        logger.error(f"Error crítico procesando edificio, abortando: {e}")
                        break
        
        if not self.extreme_mode:
            logger.info(f"✅ Completado: {len(properties)} propiedades de {processed_buildings} edificios")
        else:
            logger.info(f"⚡ FIN: {len(properties)} props")
        
        # Crear colección optimizada
        collection = PropertyCollection(
            scraped_at=datetime.now().isoformat(),
            source_url=self.search_url
        )
        
        # Agrupar propiedades por tipología para optimizar imágenes
        typology_map = {}
        
        for prop in properties:
            if hasattr(prop, '_typology_meta') and prop._typology_meta:
                typo_data = prop._typology_meta
                typo_id = self._generate_typology_id(typo_data)
                
                # Crear tipología si no existe
                if typo_id not in typology_map:
                    # Obtener imágenes de tipología + edificio (compartidas)
                    building_info = getattr(prop, '_building_info', {})
                    building_data = getattr(prop, '_building_data', {})
                    typology_images = self._extract_typology_images_with_building(typo_data, building_info, building_data)
                    
                    typology = PropertyTypology(
                        typology_id=typo_id,
                        name=typo_data.get('rooms_info', 'Departamento').replace('\n', ' ').strip(),
                        area_m2=typo_data.get('area_m2'),
                        bedrooms=typo_data.get('bedrooms'),
                        bathrooms=typo_data.get('bathrooms'),
                        property_type="Departamento",
                        images=typology_images,
                        description=typo_data.get('price_text'),
                        building_name=prop._building_name if hasattr(prop, '_building_name') else None,
                        building_location=prop.location
                    )
                    typology_map[typo_id] = typology
                
                # Limpiar metadatos temporales antes de agregar
                delattr(prop, '_typology_meta')
                if hasattr(prop, '_building_name'):
                    delattr(prop, '_building_name')
                if hasattr(prop, '_building_info'):
                    delattr(prop, '_building_info')
                if hasattr(prop, '_building_data'):
                    delattr(prop, '_building_data')
                
                # Agregar propiedad con referencia a tipología
                collection.add_property_with_typology(prop, typology_map[typo_id])
            else:
                # Propiedad sin tipología específica
                collection.properties.append(prop)
                collection.total_count += 1
        
        return collection
    
    def _navigate_to_search_page(self):
        """Navega a la página principal de búsqueda de departamentos."""
        logger.info(f"🔄 Navegando a página de búsqueda")
        self.driver.get(self.search_url)
        
        # Enable debug mode if needed
        if self.debug_mode:
            self.enable_debug_mode(True)
            self._show_debug_info(f"Navegando a página de búsqueda")
        
        # Esperar a que la página cargue según el modo
        if self.extreme_mode:
            # En modo extremo: esperar solo que aparezcan las tarjetas de edificios
            self._wait_for_element_quick("div.building-card[data-building]", timeout=2.0)
        else:
            # Modo normal: delay conservador
            self._smart_delay(2.0, 4.0)
        
        # Scroll progresivo para cargar contenido dinámico (solo si no es modo extremo)
        if not self.extreme_mode:
            if self.debug_mode:
                self._show_debug_info("Haciendo scroll para cargar contenido dinámico")
            if self.human_like_behavior:
                self.behavior.progressive_page_scroll(scroll_pause_time=1.5, num_scrolls=3)
            else:
                # Scroll rápido sin human behavior
                self.behavior.progressive_page_scroll(scroll_pause_time=0.3, num_scrolls=2)
        # En modo extremo: sin scroll, contenido ya está cargado
        
    def _extract_building_cards(self) -> List[Dict[str, Any]]:
        """
        Extrae las tarjetas de edificios según el selector de la guía:
        div.building-card[data-building]
        """
        building_cards = []
        
        try:
            # Selectores robustos con fallbacks
            card_selectors = [
                "div.building-card[data-building]",  # Selector exacto de la guía
                "[data-building]",                   # Alternativo flexible  
                "div[data-building]",                # Más específico
                ".building-card",                    # Por clase
                "[data-testid*='building']"          # Por testid si existe
            ]
            
            cards = self._find_elements_robust(card_selectors)
            logger.info(f"Encontradas {len(cards)} tarjetas de edificios")
            
            if self.debug_mode and not self.extreme_mode:
                self._show_debug_info(f"Encontradas {len(cards)} tarjetas de edificios")
                # Highlight all building cards (skip in extreme mode)
                for i, card in enumerate(cards):
                    self._highlight_element(card, "target", duration=0.3)  # Shorter duration
                    if i >= 3:  # Only highlight first 3 to avoid clutter
                        break
            
            for card in cards:
                try:
                    if self.debug_mode and not self.extreme_mode:
                        self._highlight_element(card, "highlight", duration=0.5)  # Shorter duration
                        self._show_debug_info("Extrayendo datos de tarjeta de edificio")
                    
                    building_data = self._extract_building_card_data(card)
                    if building_data:
                        building_cards.append(building_data)
                        if self.debug_mode and not self.extreme_mode:
                            self._show_debug_info(f"Edificio extraído: {building_data.get('name', 'Sin nombre')}")
                except Exception as e:
                    logger.debug(f"Error extrayendo tarjeta de edificio: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error buscando tarjetas de edificios: {e}")
        
        return building_cards
    
    def _extract_building_card_data(self, card: WebElement) -> Optional[Dict[str, Any]]:
        """
        Extrae datos de una tarjeta de edificio según la guía:
        - ID del Edificio: data-building
        - Nombre: a.text-neutral-800.lg\\:text-base
        - URL: a.text-neutral-800.lg\\:text-base href
        - Dirección: span.text-neutral-500
        - Precio desde: p.text-lg.font-bold
        - Imagen: li.splide__slide.is-visible img src
        - Promociones: div.badge_promos span
        """
        try:
            building_data = {}
            
            # ID del Edificio
            building_data['building_id'] = card.get_attribute('data-building')
            
            # Nombre del Edificio y URL con selectores robustos
            name_link_selectors = [
                "a.text-neutral-800.lg\\:text-base",  # Selector exacto de la guía
                "a[href*='/edificio/']",               # Por URL de edificio
                "a.text-neutral-800",                  # Sin breakpoint lg
                "h3 a, h2 a, h1 a",                  # Enlaces en títulos
                "a[class*='text-neutral']",           # Por clase parcial
                "a:first-of-type"                     # Primer enlace como fallback
            ]
            
            name_link = self._find_element_robust(name_link_selectors, card)
            if name_link:
                building_data['name'] = name_link.text.strip()
                building_data['url'] = name_link.get_attribute('href')
            else:
                logger.debug("No se encontró enlace del edificio")
                return None
            
            # Dirección con selectores robustos
            address_selectors = [
                "span.text-neutral-500",        # Selector exacto de la guía
                "span.text-gray-500",           # Variación de color
                "span[class*='text-neutral']",  # Por clase parcial
                "span[class*='text-gray']",     # Alternativa gray
                ".address, .location"           # Por clases semánticas
            ]
            address_elem = self._find_element_robust(address_selectors, card)
            building_data['address'] = address_elem.text.strip() if address_elem else None
            
            # Precio "Desde" con selectores robustos
            price_selectors = [
                "p.text-lg.font-bold",          # Selector exacto de la guía
                "p[class*='font-bold']",        # Por clase parcial
                "span.text-lg.font-bold",       # Como span
                ".price, .precio",              # Por clases semánticas
                "p[class*='text-lg']"           # Por tamaño de texto
            ]
            price_elem = self._find_element_robust(price_selectors, card)
            building_data['price_from'] = price_elem.text.strip() if price_elem else None
            
            # URL de Imagen con selectores robustos
            img_selectors = [
                "li.splide__slide.is-visible img",  # Selector exacto de la guía
                "li.splide__slide img",             # Sin estado visible
                ".splide__slide img",               # Sin li
                "img[src*='assetplan']",            # Por dominio
                "img:first-of-type"                 # Primera imagen
            ]
            img_elem = self._find_element_robust(img_selectors, card)
            building_data['image_url'] = img_elem.get_attribute('src') if img_elem else None
            
            # Promociones con selectores robustos
            promo_selectors = [
                "div.badge_promos span",      # Selector exacto de la guía
                ".badge_promos span",         # Sin div
                "span.badge_promos",          # Directamente en span
                "[class*='badge'] span",      # Por clase parcial
                ".promo, .promocion"          # Por clases semánticas
            ]
            promo_elements = self._find_elements_robust(promo_selectors, card)
            building_data['promotions'] = [elem.text.strip() for elem in promo_elements if elem.text.strip()]
            
            # Verificar disponibilidad de tipologías
            building_data['available_types'] = self._check_available_typologies(card)
            
            return building_data
            
        except Exception as e:
            logger.error(f"Error extrayendo datos de tarjeta de edificio: {e}")
            return None
    
    def _check_available_typologies(self, card: WebElement) -> List[Dict[str, Any]]:
        """
        Verifica disponibilidad de tipologías según la guía:
        - Enlaces sin clase 'grayscale' están disponibles
        - Enlaces con clase 'grayscale' no están disponibles
        """
        available_types = []
        
        try:
            # Buscar enlaces de tipologías
            type_links = card.find_elements(By.CSS_SELECTOR, "div.space-y-1\\.5 > a")
            
            for link in type_links:
                try:
                    # Verificar si tiene clase grayscale
                    classes = link.get_attribute('class') or ''
                    is_available = 'grayscale' not in classes
                    
                    if is_available:
                        type_data = {
                            'url': link.get_attribute('href'),
                            'text': link.text.strip(),
                            'available': True
                        }
                        available_types.append(type_data)
                except Exception as e:
                    logger.debug(f"Error verificando tipología: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"Error buscando tipologías: {e}")
        
        return available_types
    
    def _process_building(self, building_data: Dict[str, Any], max_props: int) -> List[Property]:
        """
        Procesa un edificio completo para extraer sus departamentos.
        Sigue el flujo: edificio -> tipologías -> departamentos
        """
        properties = []
        building_url = building_data.get('url')
        
        if not building_url:
            return properties
        
        try:
            # Navegar al edificio con medición de tiempo
            import time
            start_time = time.time()
            logger.debug(f"Navegando al edificio: {building_data.get('name', 'Unknown')}")
            self.driver.get(building_url)
            nav_time = time.time() - start_time
            logger.info(f"⏱️ Navegación al edificio: {nav_time:.2f}s")
            
            delay_start = time.time()
            self._smart_delay(2.0, 3.0)
            delay_time = time.time() - delay_start
            logger.info(f"⏱️ Delay post-navegación: {delay_time:.2f}s")
            
            # Extraer información general del edificio
            info_start = time.time()
            building_info = self._extract_building_detail_info()
            info_time = time.time() - info_start
            logger.info(f"⏱️ Extracción info edificio: {info_time:.2f}s")
            
            # Extraer tipologías de departamentos
            typo_start = time.time()
            typologies = self._extract_building_typologies()
            typo_time = time.time() - typo_start
            logger.info(f"⏱️ Extracción tipologías: {typo_time:.2f}s")
            logger.debug(f"Encontradas {len(typologies)} tipologías en el edificio")
            
            # Procesar cada tipología
            for i, typology in enumerate(typologies):
                if len(properties) >= max_props:
                    break
                
                typo_proc_start = time.time()
                remaining = max_props - len(properties)
                typology_props = self._process_typology(typology, building_info, building_data, remaining)
                typo_proc_time = time.time() - typo_proc_start
                logger.info(f"⏱️ Tipología {i+1}: {typo_proc_time:.2f}s (+{len(typology_props)} props)")
                properties.extend(typology_props)
                
                # Delay entre tipologías
                self._smart_delay(0.5, 1.0)
                
        except Exception as e:
            logger.error(f"Error procesando edificio {building_url}: {e}")
        
        return properties
    
    def _extract_building_detail_info(self) -> Dict[str, Any]:
        """
        Extrae información general del edificio según la guía:
        - Nombre: h1.name-building
        - Dirección: h2.address-building  
        - URLs de Galería: section.galery-desktop img src
        - Comodidades: div.flex.flex-row.items-center p.text-sm
        """
        building_info = {}
        
        try:
            # Nombre del edificio
            try:
                name_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.name-building")
                building_info['name'] = name_elem.text.strip()
            except NoSuchElementException:
                building_info['name'] = None
            
            # Dirección
            try:
                address_elem = self.driver.find_element(By.CSS_SELECTOR, "h2.address-building")
                building_info['address'] = address_elem.text.strip()
            except NoSuchElementException:
                building_info['address'] = None
            
            # URLs de galería
            try:
                gallery_imgs = self.driver.find_elements(By.CSS_SELECTOR, "section.galery-desktop img")
                building_info['gallery_urls'] = [img.get_attribute('src') for img in gallery_imgs]
            except NoSuchElementException:
                building_info['gallery_urls'] = []
            
            # Comodidades
            try:
                amenity_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-row.items-center p.text-sm")
                building_info['amenities'] = [elem.text.strip() for elem in amenity_elements]
            except NoSuchElementException:
                building_info['amenities'] = []
                
        except Exception as e:
            logger.error(f"Error extrayendo información del edificio: {e}")
        
        return building_info
    
    def _extract_building_typologies(self) -> List[Dict[str, Any]]:
        """
        Extrae tipologías de departamentos según la guía:
        Selector: div.grid.grid-cols-1.gap-6 > div
        """
        typologies = []
        
        try:
            # Selector exacto de la guía
            typology_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.grid.grid-cols-1.gap-6 > div")
            
            for card in typology_cards:
                try:
                    typology_data = self._extract_typology_card_data(card)
                    if typology_data:
                        typologies.append(typology_data)
                except Exception as e:
                    logger.debug(f"Error extrayendo tipología: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error buscando tipologías: {e}")
        
        return typologies
    
    def _extract_typology_card_data(self, card: WebElement) -> Optional[Dict[str, Any]]:
        """
        Extrae datos de una tarjeta de tipología según la guía:
        - URL de Imagen: img.object-cover src
        - Dormitorios y Baños: div.flex.gap-x-2\\.5 text
        - Superficie: div.flex.flex-col.space-y-1 text
        - Valor de Arriendo: p.text-lg.font-semibold text
        - Promociones: div.badge_promos span text
        - URL para Ver Unidades: a[href*="/arriendo/departamento/"] href
        - Cantidad de Unidades: a[href*="/arriendo/departamento/"] text
        """
        try:
            typology_data = {}
            
            # URL de imagen
            try:
                img_elem = card.find_element(By.CSS_SELECTOR, "img.object-cover")
                typology_data['image_url'] = img_elem.get_attribute('src')
            except NoSuchElementException:
                typology_data['image_url'] = None
            
            # Dormitorios y Baños
            try:
                rooms_elem = card.find_element(By.CSS_SELECTOR, "div.flex.gap-x-2\\.5")
                rooms_text = rooms_elem.text.strip()
                typology_data['rooms_info'] = rooms_text
                
                # Parsear dormitorios y baños
                typology_data['bedrooms'] = self._parse_bedrooms(rooms_text)
                typology_data['bathrooms'] = self._parse_bathrooms(rooms_text)
            except NoSuchElementException:
                typology_data['rooms_info'] = None
                typology_data['bedrooms'] = None
                typology_data['bathrooms'] = None
            
            # Superficie
            try:
                area_elem = card.find_element(By.CSS_SELECTOR, "div.flex.flex-col.space-y-1")
                area_text = area_elem.text.strip()
                typology_data['area_text'] = area_text
                typology_data['area_m2'] = self._parse_area(area_text)
            except NoSuchElementException:
                typology_data['area_text'] = None
                typology_data['area_m2'] = None
            
            # Valor de arriendo
            try:
                price_elem = card.find_element(By.CSS_SELECTOR, "p.text-lg.font-semibold")
                price_text = price_elem.text.strip()
                typology_data['price_text'] = price_text
                typology_data['price_uf'] = self._parse_price_uf(price_text)
            except NoSuchElementException:
                typology_data['price_text'] = None
                typology_data['price_uf'] = None
            
            # Promociones
            try:
                promo_elements = card.find_elements(By.CSS_SELECTOR, "div.badge_promos span")
                typology_data['promotions'] = [elem.text.strip() for elem in promo_elements]
            except NoSuchElementException:
                typology_data['promotions'] = []
            
            # URL para ver unidades y cantidad
            try:
                units_link = card.find_element(By.CSS_SELECTOR, "a[href*='/arriendo/departamento/']")
                typology_data['units_url'] = units_link.get_attribute('href')
                typology_data['units_text'] = units_link.text.strip()
                typology_data['units_count'] = self._parse_units_count(units_link.text.strip())
            except NoSuchElementException:
                typology_data['units_url'] = None
                typology_data['units_text'] = None
                typology_data['units_count'] = 0
            
            return typology_data
            
        except Exception as e:
            logger.error(f"Error extrayendo datos de tipología: {e}")
            return None
    
    def _process_typology(self, typology: Dict[str, Any], building_info: Dict[str, Any], 
                         building_data: Dict[str, Any], max_props: int) -> List[Property]:
        """
        Procesa una tipología para extraer departamentos individuales.
        Maneja los casos A (1 unidad) y B (múltiples unidades) según la guía.
        """
        properties = []
        units_count = typology.get('units_count', 0)
        units_url = typology.get('units_url')
        
        if not units_url or units_count == 0:
            return properties
        
        try:
            if units_count == 1:
                # Caso A: Navegación directa (1 unidad)
                if len(properties) < max_props:
                    prop = self._extract_single_unit_direct(typology, building_info, building_data)
                    if prop:
                        properties.append(prop)
            else:
                # Caso B: Modal con múltiples unidades
                try:
                    remaining = max_props - len(properties)
                    if remaining > 0:
                        props = self._extract_multiple_units_modal(typology, building_info, building_data, remaining)
                        properties.extend(props)
                except Exception as modal_error:
                    logger.error(f"Error en modal, saltando tipología: {modal_error}")
                    # Intentar volver a una página estable
                    try:
                        import time
                        self.driver.back()
                        time.sleep(1)
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Error procesando tipología: {e}")
        
        return properties
    
    def _extract_single_unit_direct(self, typology: Dict[str, Any], building_info: Dict[str, Any],
                                   building_data: Dict[str, Any]) -> Optional[Property]:
        """
        Caso A: Extrae unidad única con navegación directa.
        """
        try:
            units_url = typology.get('units_url')
            if not units_url:
                return None
            
            # Navegar directamente al departamento
            self.driver.get(units_url)
            self._smart_delay(1.5, 2.5)
            
            # Extraer datos completos del departamento
            property_data = self._extract_department_detail_page()
            
            # Crear objeto Property
            result = self._create_property_from_data(property_data, typology, building_info, building_data)
            if result:
                prop, typology_meta = result
                # Almacenar metadatos temporalmente (no en el modelo Pydantic)
                prop._typology_meta = typology_meta
                prop._building_name = building_info.get('name')
                prop._building_info = building_info
                prop._building_data = building_data
                return prop
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo unidad directa: {e}")
            return None
    
    def _extract_multiple_units_modal(self, typology: Dict[str, Any], building_info: Dict[str, Any],
                                     building_data: Dict[str, Any], max_properties_remaining: int) -> List[Property]:
        """
        Caso B: Extrae múltiples unidades navegando a modal.
        El flujo real es: edificio -> URL con ?showUnits=true -> seleccionar unidad -> URL con ?selectedUnit=X
        """
        properties = []
        
        # Timeout total para la función en modo extremo
        import signal
        total_timeout = 15 if self.extreme_mode else 60
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Timeout de {total_timeout}s en modal")
        
        if self.extreme_mode:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(total_timeout)
        
        try:
            import time
            step_start = time.time()
            logger.info("🔍 [1/6] Iniciando búsqueda de botón modal")
            
            # Buscar botón de tipología (los botones reales que existen)
            button_selectors = [
                "a[href*='/arriendo/departamento/'][href*='/home-inclusive-independencia/']:not([href*='mapa'])",  # Botones de tipología específicos
                "a[class*='bg-blue']:not([href*='mapa']):not([href*='javascript'])",    # Por clase parcial sin mapa ni JS
                "a.bg-blue-600:not([href*='mapa'])",          # Excluir explícitamente botones de mapa
                "a.text-white.hover\\:bg-blue-700:not([href*='mapa'])",  # Por clases completas sin mapa
                "a[class*='bg-blue'][class*='text-white']:not([href*='mapa'])"  # Combinación sin mapa
            ]
            
            search_time = time.time() - step_start
            logger.info(f"🔍 [1/6] Selectores preparados en {search_time:.2f}s")
            
            units_button = None
            # Usar timeout ultra-agresivo en modo extremo
            wait_timeout = 0.5 if self.extreme_mode else 15
            search_wait = WebDriverWait(self.driver, wait_timeout)
            
            # Verificación rápida previa: ¿hay algún botón azul en la página?
            quick_check_start = time.time()
            quick_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[class*='bg-blue']")
            quick_check_time = time.time() - quick_check_start
            logger.info(f"🔍 [2a/6] Verificación rápida: {len(quick_buttons)} botones azules en {quick_check_time:.2f}s")
            
            # Debug: mostrar URLs de los botones encontrados
            if self.debug_mode and len(quick_buttons) > 0:
                for i, btn in enumerate(quick_buttons[:3]):  # Solo primeros 3
                    try:
                        href = btn.get_attribute('href') or 'sin-href'
                        text = btn.text.strip() or 'sin-texto'
                        logger.info(f"🔍 [2a/6] Botón {i+1}: {text} -> {href}")
                    except:
                        pass
            
            if len(quick_buttons) == 0:
                logger.info("❌ [2a/6] No hay botones azules, saltando búsqueda detallada")
                raise Exception("No hay botones disponibles en esta página")
            
            step_start = time.time()
            logger.info(f"🔍 [2/6] Buscando botón específico con timeout {wait_timeout}s")
            
            for i, selector in enumerate(button_selectors):
                try:
                    selector_start = time.time()
                    units_button = search_wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    selector_time = time.time() - selector_start
                    logger.info(f"✅ [2/6] Botón encontrado con selector {i+1} en {selector_time:.2f}s: {selector}")
                    
                    if self.debug_mode and not self.extreme_mode:
                        self._highlight_element(units_button, "target", duration=2.0)
                        self._show_debug_info(f"Botón modal encontrado: {selector}")
                    break
                except TimeoutException:
                    selector_time = time.time() - selector_start
                    logger.info(f"❌ [2/6] Selector {i+1} falló en {selector_time:.2f}s: {selector}")
                    continue
            
            button_search_time = time.time() - step_start
            logger.info(f"🔍 [2/6] Búsqueda de botón completada en {button_search_time:.2f}s")
            
            if not units_button:
                if self.debug_mode:
                    self._show_debug_info("ERROR: No se encontró botón de modal")
                raise Exception("No se pudo encontrar el botón para abrir modal de unidades")
            
            step_start = time.time()
            logger.info("🔍 [3/6] Preparando click en botón modal")
            
            if self.debug_mode:
                self._highlight_element(units_button, "clicked", duration=1.0)
                self._show_debug_info("Haciendo clic en botón de modal")
                self._monitor_navigation("antes-clic-modal")
            
            self._debug_click(units_button, "modal-units")
            click_time = time.time() - step_start
            logger.info(f"✅ [3/6] Modal clickeado en {click_time:.2f}s")
            
            # Monitor navigation immediately after click
            if self.debug_mode:
                self._smart_delay(1.0, 2.0)  # Short delay to see immediate effect
                self._monitor_navigation("despues-clic-modal")
            
            # Wait for navigation with mode-aware timeout  
            step_start = time.time()
            timeout = 3.0 if self.extreme_mode else 15.0
            logger.info(f"🔍 [4/6] Esperando navegación a tipología con timeout {timeout}s")
            
            # Cambiar pattern: estos botones llevan a tipología, no modal
            navigation_success = self._wait_for_navigation_with_debug(
                expected_url_pattern="/arriendo/departamento/", 
                timeout=timeout, 
                context="typology-navigation"
            )
            
            nav_time = time.time() - step_start
            logger.info(f"🔍 [4/6] Navegación completada en {nav_time:.2f}s (éxito: {navigation_success})")
            
            if not navigation_success:
                current_url = self.driver.current_url
                if "mapa" in current_url:
                    logger.error("ERROR: Navegó a mapa en lugar de modal")
                    self._show_debug_info("ERROR: Click en 'Ver Mapa'")
                    raise Exception("Se detectó navegación incorrecta a mapa")
                else:
                    logger.error("NAVEGACION FALLIDA: no se detectó showUnits=true en URL")
                    self._show_debug_info("ERROR: No navegó a modal")
                    raise Exception("No se detectó navegación al modal después del clic")
            
            # Verificar si hay error 500 antes de procesar (retry sin refresh)
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                if "500" in page_text or "internal server error" in page_text:
                    logger.warning("ERROR 500 detectado, puede ser temporal - esperando 2s")
                    self._show_debug_info("ERROR 500: Esperando...")
                    import time
                    time.sleep(2)  # Esperar 2 segundos sin refresh
                    
                    # Segunda verificación sin refresh
                    try:
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                        if "500" in page_text or "internal server error" in page_text:
                            logger.warning("ERROR 500 persistente, continuando de todos modos...")
                            # Continuar en lugar de abortar - la página puede seguir funcionando
                        else:
                            logger.info("✅ ERROR 500 resuelto")
                    except:
                        pass
            except Exception as e:
                # Si no se puede verificar el contenido, log pero continuar
                logger.debug(f"No se pudo verificar contenido de página: {e}")
            
            # Esperar a que navegue y el modal aparezca con múltiples indicadores
            modal_selectors = [
                "div[x-show='show']",                           # Selector Alpine.js exacto
                "div.transition-all.transform.bg-white",        # Por clases del modal
                "ul.divide-y.divide-gray-200",                  # Lista de unidades
                "div.fixed.inset-0.transition-all.transform"    # Overlay del modal
            ]
            
            modal_loaded = False
            successful_selector = None
            
            for selector in modal_selectors:
                try:
                    logger.info(f"PROBANDO SELECTOR MODAL: {selector}")
                    self._get_wait().until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    modal_loaded = True
                    successful_selector = selector
                    logger.info(f"MODAL DETECTADO: selector {selector} exitoso")
                    if self.debug_mode:
                        self._show_debug_info(f"Modal encontrado: {selector}")
                    break
                except TimeoutException:
                    logger.warning(f"SELECTOR FALLIDO: {selector} no encontrado")
                    if self.debug_mode:
                        self._show_debug_info(f"Selector falló: {selector}")
                    continue
            
            if not modal_loaded:
                logger.error("MODAL NO DETECTADO: ningún selector funcionó")
                if self.debug_mode:
                    self._show_debug_info("ERROR: Modal no detectado")
                    self._monitor_navigation("modal-no-encontrado")
                raise Exception("No se pudo detectar que el modal se cargó correctamente")
            
            # Esperar adicional para que termine la animación del modal (duration-300)
            logger.info(f"MODAL CARGADO: esperando animación con selector {successful_selector}")
            if self.debug_mode:
                self._show_debug_info("Modal cargado, esperando animación...")
            self._smart_delay(1.0, 2.0)
            
            # Extraer unidades del modal usando el selector real
            try:
                unit_items = self.driver.find_elements(By.CSS_SELECTOR, "ul.divide-y.divide-gray-200 > li")
                logger.debug(f"Encontradas {len(unit_items)} unidades en modal")
                
                # Procesar cada unidad sin mantener referencias a elementos stale
                for i in range(len(unit_items)):
                    # CONTROL DEL LÍMITE: Detener si ya tenemos suficientes propiedades
                    if len(properties) >= max_properties_remaining:
                        logger.info(f"🛑 Límite alcanzado: {len(properties)}/{max_properties_remaining} propiedades")
                        break
                    
                    try:
                        # Re-localizar la lista cada vez para evitar stale elements
                        unit_items = self.driver.find_elements(By.CSS_SELECTOR, "ul.divide-y.divide-gray-200 > li")
                        
                        if i >= len(unit_items):
                            logger.debug(f"Índice {i} fuera de rango, terminando procesamiento de unidades")
                            break
                            
                        item = unit_items[i]
                        
                        # Extraer datos básicos antes del clic (mientras el elemento es válido)
                        unit_basic_data = self._extract_unit_from_modal(item)
                        if not unit_basic_data:
                            logger.debug(f"No se pudieron extraer datos de unidad {i+1}")
                            continue
                        
                        # Hacer clic para seleccionar la unidad
                        try:
                            label = item.find_element(By.CSS_SELECTOR, "label")
                            current_url_before = self.driver.current_url
                            self._debug_click(label, "typology-label")
                            
                            # CRÍTICO: Esperar navegación COMPLETA antes de continuar al siguiente item
                            navigation_success = self._wait_for_complete_navigation(
                                initial_url=current_url_before,
                                timeout=5.0 if self.extreme_mode else 8.0
                            )
                            
                            if not navigation_success:
                                logger.warning(f"❌ Navegación no completada para unidad {i+1}, saltando")
                                continue
                                
                        except (StaleElementReferenceException, NoSuchElementException) as e:
                            logger.debug(f"Error haciendo clic en unidad {i+1}: {e}")
                            continue
                        
                        # Verificar si cambió la URL (debe contener selectedUnit)
                        current_url = self.driver.current_url
                        if "selectedUnit=" in current_url:
                            # Extraer datos completos del departamento
                            property_data = self._extract_department_detail_page()
                            
                            # Crear objeto Property
                            result = self._create_property_from_data(property_data, typology, building_info, building_data, unit_basic_data)
                            if result:
                                prop, typology_meta = result
                                # Almacenar metadatos temporalmente (no en el modelo Pydantic)
                                prop._typology_meta = typology_meta
                                prop._building_name = building_info.get('name')
                                prop._building_info = building_info
                                prop._building_data = building_data
                                properties.append(prop)
                                logger.info(f"🏠 AGREGADA propiedad #{len(properties)}: {unit_basic_data.get('apartment_number', 'N/A')}")
                                if not self.extreme_mode:
                                    logger.debug(f"Extraída unidad {i+1}: {unit_basic_data.get('apartment_number', 'N/A')}")
                            else:
                                logger.warning(f"❌ Propiedad NO creada para unidad {i+1}")
                        
                        # Log timing para debug (solo si no es extremo)
                        back_start = time.time() if self.extreme_mode else None
                        
                        # CRÍTICO: Delay más largo para evitar clicks múltiples
                        if self.extreme_mode:
                            time.sleep(0.5)  # Aumentado de 0.2s a 0.5s
                        else:
                            self._smart_delay(1.0, 2.0)  # Aumentado para mayor estabilidad
                        
                        # Estrategia inteligente para volver al modal
                        if self.extreme_mode:
                            # En modo extremo: usar history.back() si es más rápido
                            self._smart_back_to_modal()
                        else:
                            # Modo normal: navegación manual confiable
                            modal_url = current_url.split('&selectedUnit=')[0].split('?selectedUnit=')[0]
                            if '?' not in modal_url:
                                modal_url += "?showUnits=true"
                            elif "showUnits=true" not in modal_url:
                                modal_url += "&showUnits=true"
                            
                            self.driver.get(modal_url)
                            self._smart_delay(1.0, 2.0)
                        
                        # Log timing después de navegación (solo cada 5 unidades en extremo)
                        if self.extreme_mode and back_start and (i+1) % 5 == 0:
                            nav_time = time.time() - back_start
                            logger.info(f"⚡ [{i+1}] Nav: {nav_time:.2f}s")
                        
                        # Esperar a que el modal se recargue
                        try:
                            wait_start = time.time() if self.extreme_mode else None
                            self._get_wait().until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.divide-y.divide-gray-200"))
                            )
                            if self.extreme_mode and wait_start and (i+1) % 5 == 0:
                                wait_time = time.time() - wait_start
                                logger.info(f"⚡ [{i+1}] Wait: {wait_time:.2f}s")
                        except TimeoutException:
                            logger.warning(f"No se pudo re-localizar lista de unidades después de procesar unidad {i+1}")
                            break
                        
                    except Exception as e:
                        logger.debug(f"Error procesando unidad individual {i+1}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error procesando unidades del modal: {e}")
                
        except Exception as e:
            logger.error(f"Error navegando a modal de unidades: {e}")
        
        finally:
            # Limpiar timeout si está activo
            if self.extreme_mode:
                signal.alarm(0)
        
        return properties
    
    def _extract_unit_from_modal(self, item: WebElement) -> Dict[str, Any]:
        """
        Extrae datos de una unidad desde el modal según la estructura real:
        - ID Interno: input[type="radio"] value
        - Número del Depto: p.text-lg.font-bold.text-gray-800 text
        - Precio actual: span.text-lg.font-bold.text-gray-800 text (segundo span)
        - Precio tachado: span.text-xs.font-bold.text-gray-400.line-through text
        - Disponibilidad: div.chip-available text
        - Detalles: p.text-sm.text-gray-600 text (área, baños, piso)
        """
        unit_data = {}
        
        try:
            # ID interno
            try:
                radio_input = item.find_element(By.CSS_SELECTOR, "input[type='radio']")
                unit_data['internal_id'] = radio_input.get_attribute('value')
            except NoSuchElementException:
                unit_data['internal_id'] = None
            
            # Número del departamento (primer p.text-lg.font-bold)
            try:
                number_elem = item.find_element(By.CSS_SELECTOR, "p.text-lg.font-bold.text-gray-800")
                unit_data['apartment_number'] = number_elem.text.strip()
            except NoSuchElementException:
                unit_data['apartment_number'] = None
            
            # Precio actual (segundo span con text-lg.font-bold)
            try:
                price_elements = item.find_elements(By.CSS_SELECTOR, "span.text-lg.font-bold.text-gray-800")
                if price_elements:
                    # Tomar el último span que suele ser el precio actual
                    unit_data['monthly_price'] = price_elements[-1].text.strip()
                else:
                    unit_data['monthly_price'] = None
            except NoSuchElementException:
                unit_data['monthly_price'] = None
            
            # Precio original tachado
            try:
                original_price_elem = item.find_element(By.CSS_SELECTOR, "span.text-xs.font-bold.text-gray-400.line-through")
                unit_data['original_price'] = original_price_elem.text.strip()
            except NoSuchElementException:
                unit_data['original_price'] = None
            
            # Disponibilidad
            try:
                availability_elem = item.find_element(By.CSS_SELECTOR, "div.chip-available")
                unit_data['availability'] = availability_elem.text.strip()
            except NoSuchElementException:
                unit_data['availability'] = None
            
            # Detalles (área, baños, piso)
            try:
                details_elements = item.find_elements(By.CSS_SELECTOR, "p.text-sm.text-gray-600")
                unit_data['details'] = [elem.text.strip() for elem in details_elements if elem.text.strip()]
            except NoSuchElementException:
                unit_data['details'] = []
            
            # Extraer área y piso de los detalles
            unit_data['area_m2'] = None
            unit_data['floor'] = None
            for detail in unit_data.get('details', []):
                # Extraer área
                if 'm²' in detail:
                    area_match = re.search(r'(\d+)\s*m²', detail)
                    if area_match:
                        try:
                            unit_data['area_m2'] = float(area_match.group(1))
                        except:
                            pass
                
                # Extraer piso
                if 'Piso' in detail:
                    floor_match = re.search(r'Piso\s*(\d+)', detail, re.IGNORECASE)
                    if floor_match:
                        try:
                            floor = int(floor_match.group(1))
                            if 1 <= floor <= 50:  # Validar rango razonable
                                unit_data['floor'] = floor
                                logger.debug(f"🏢 Piso extraído del modal: {floor} (detalle: '{detail}')")
                        except:
                            pass
            
            # Promociones
            try:
                promo_elements = item.find_elements(By.CSS_SELECTOR, "span.badge_promos")
                unit_data['promotions'] = [elem.text.strip() for elem in promo_elements if elem.text.strip()]
            except NoSuchElementException:
                unit_data['promotions'] = []
                
        except Exception as e:
            logger.error(f"Error extrayendo datos de unidad del modal: {e}")
        
        return unit_data
    
    def _extract_department_detail_page(self) -> Dict[str, Any]:
        """
        Extrae datos completos de la página de detalle del departamento según la guía:
        - Nombre de Comunidad: h1.title-breadcrumbs
        - Número del Depto: #info > div:nth-child(3) > span.text-xl
        - Dirección: #info > div:nth-child(3) > span.text-xs
        - Valor Arriendo Original: span.line-through
        - Valor Arriendo Descuento: XPath específico
        - Gasto Común: XPath específico
        - Garantía: XPath específico
        - Promociones: div.badge_promos span.inline-flex
        - URLs de Imágenes: ul.splide__list img src
        """
        detail_data = {}
        
        try:
            # Nombre de comunidad
            try:
                community_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.title-breadcrumbs")
                detail_data['community_name'] = community_elem.text.strip()
            except NoSuchElementException:
                detail_data['community_name'] = None
            
            # Número del departamento
            try:
                number_elem = self.driver.find_element(By.CSS_SELECTOR, "#info > div:nth-child(3) > span.text-xl")
                detail_data['apartment_number'] = number_elem.text.strip()
            except NoSuchElementException:
                detail_data['apartment_number'] = None
            
            # Dirección
            try:
                address_elem = self.driver.find_element(By.CSS_SELECTOR, "#info > div:nth-child(3) > span.text-xs")
                detail_data['address'] = address_elem.text.strip()
            except NoSuchElementException:
                detail_data['address'] = None
            
            # Valor arriendo original
            try:
                original_price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.line-through")
                detail_data['original_price'] = original_price_elem.text.strip()
            except NoSuchElementException:
                detail_data['original_price'] = None
            
            # Valor arriendo con descuento (usando XPath según la guía)
            try:
                discount_price_elem = self.driver.find_element(By.XPATH, "//p[contains(text(), 'OFF')]/following-sibling::span")
                detail_data['discount_price'] = discount_price_elem.text.strip()
            except NoSuchElementException:
                detail_data['discount_price'] = None
            
            # Gasto común
            try:
                common_expense_elem = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Gasto común')]/following-sibling::span")
                detail_data['common_expense'] = common_expense_elem.text.strip()
            except NoSuchElementException:
                detail_data['common_expense'] = None
            
            # Garantía
            try:
                guarantee_elem = self.driver.find_element(By.XPATH, "//span[text()='Garantía']/following-sibling::span")
                detail_data['guarantee'] = guarantee_elem.text.strip()
            except NoSuchElementException:
                detail_data['guarantee'] = None
            
            # Promociones
            try:
                promo_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.badge_promos span.inline-flex")
                detail_data['promotions'] = [elem.text.strip() for elem in promo_elements]
            except NoSuchElementException:
                detail_data['promotions'] = []
            
            # URLs de imágenes
            try:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.splide__list img")
                detail_data['image_urls'] = [img.get_attribute('src') for img in img_elements if img.get_attribute('src')]
                # Filtrar duplicados
                detail_data['image_urls'] = list(set(detail_data['image_urls']))
            except NoSuchElementException:
                detail_data['image_urls'] = []
            
            # Extraer piso
            detail_data['floor'] = self._extract_floor_from_page()
            
            # Intentar extraer información adicional de las pestañas (saltear en modo extremo)
            if not self.extreme_mode:
                detail_data.update(self._extract_detail_tabs())
            
        except Exception as e:
            logger.error(f"Error extrayendo datos de página de detalle: {e}")
        
        return detail_data
    
    def _extract_detail_tabs(self) -> Dict[str, Any]:
        """
        Extrae información de las pestañas de detalle según la guía:
        - Sección "Detalle" (id="detail")
        - Sección "Características" (id="features")
        """
        tab_data = {}
        
        try:
            # Hacer clic en pestaña "Detalle" si existe
            try:
                detail_tab = self.driver.find_element(By.CSS_SELECTOR, "nav#sticky-menu a[href*='detail']")
                self._debug_click(detail_tab, "detail-tab")
                self._smart_delay(0.5, 1.0)
                
                # Extraer datos de la sección detalle
                detail_section = self.driver.find_element(By.CSS_SELECTOR, "#detail")
                
                # Código del departamento
                try:
                    code_elem = detail_section.find_element(By.CSS_SELECTOR, "div.cod-dpt span")
                    tab_data['apartment_code'] = code_elem.text.strip()
                except NoSuchElementException:
                    tab_data['apartment_code'] = None
                
                # Disponibilidad
                try:
                    availability_elem = detail_section.find_element(By.CSS_SELECTOR, "div.chip-available")
                    tab_data['availability'] = availability_elem.text.strip()
                except NoSuchElementException:
                    tab_data['availability'] = None
                
                # Características (features)
                try:
                    feature_elements = detail_section.find_elements(By.CSS_SELECTOR, "div.item-feature")
                    tab_data['features'] = [elem.text.strip() for elem in feature_elements]
                except NoSuchElementException:
                    tab_data['features'] = []
                    
            except NoSuchElementException:
                pass
            
            # Hacer clic en pestaña "Características" si existe
            try:
                features_tab = self.driver.find_element(By.CSS_SELECTOR, "nav#sticky-menu a[href*='features']")
                self._debug_click(features_tab, "features-tab")
                self._smart_delay(0.5, 1.0)
                
                # Hacer clic en "Mostrar más" si existe
                try:
                    show_more = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Mostrar más')]")
                    self._debug_click(show_more, "show-more")
                    self._smart_delay(0.5, 1.0)
                except NoSuchElementException:
                    pass
                
                # Extraer terminaciones
                try:
                    finishes_elements = self.driver.find_elements(By.XPATH, "//h2[text()='Terminaciones']/following-sibling::ul/li")
                    tab_data['finishes'] = [elem.text.strip() for elem in finishes_elements]
                except NoSuchElementException:
                    tab_data['finishes'] = []
                
                # Extraer equipamiento
                try:
                    equipment_elements = self.driver.find_elements(By.XPATH, "//h2[text()='Equipamiento']/following-sibling::ul/li")
                    tab_data['equipment'] = [elem.text.strip() for elem in equipment_elements]
                except NoSuchElementException:
                    tab_data['equipment'] = []
                
                # Extraer comodidades del edificio
                try:
                    amenities_elements = self.driver.find_elements(By.XPATH, "//h3[contains(text(), 'Comodidades del edificio')]//div[@class='grid']/div")
                    tab_data['building_amenities'] = [elem.text.strip() for elem in amenities_elements]
                except NoSuchElementException:
                    tab_data['building_amenities'] = []
                    
            except NoSuchElementException:
                pass
                
        except Exception as e:
            logger.debug(f"Error extrayendo datos de pestañas: {e}")
        
        return tab_data
    
    def _create_property_from_data(self, property_data: Dict[str, Any], typology: Dict[str, Any],
                                 building_info: Dict[str, Any], building_data: Dict[str, Any],
                                 unit_data: Optional[Dict[str, Any]] = None) -> Optional[Property]:
        """
        Crea un objeto Property a partir de todos los datos extraídos.
        Incluye validaciones para asegurar calidad de datos.
        """
        try:
            # Validaciones de calidad de datos
            current_url = self.driver.current_url
            logger.debug(f"🏠 Creando propiedad desde URL: {current_url}")
            logger.debug(f"🏠 Property data keys: {list(property_data.keys()) if property_data else 'None'}")
            logger.debug(f"🏠 Typology data keys: {list(typology.keys()) if typology else 'None'}")
            
            # Validación básica: debe tener al menos un nombre o URL válida
            identification_sources = [
                property_data.get('community_name'),
                building_info.get('name'),
                building_data.get('name'),
                current_url
            ]
            if not any(identification_sources):
                logger.warning(f"❌ Propiedad rechazada: sin información básica de identificación. Sources: {identification_sources}")
                return None
            
            # Validación de URL: debe ser de AssetPlan
            if not current_url or 'assetplan.cl' not in current_url:
                logger.warning(f"❌ Propiedad rechazada: URL inválida: {current_url}")
                return None
            
            # Validación de precio: al menos uno debe existir
            price_sources = [
                property_data.get('discount_price'),
                property_data.get('original_price'),
                unit_data and unit_data.get('monthly_price') if unit_data else False,
                typology.get('price_text')
            ]
            has_price = any(price_sources)
            
            if not has_price:
                logger.warning(f"❌ Propiedad rechazada: sin información de precio. Sources: {price_sources}")
                return None
            # Determinar título
            title_parts = []
            if property_data.get('community_name'):
                title_parts.append(property_data['community_name'])
            if unit_data and unit_data.get('apartment_number'):
                title_parts.append(f"Depto {unit_data['apartment_number']}")
            elif property_data.get('apartment_number'):
                title_parts.append(f"Depto {property_data['apartment_number']}")
            elif building_info.get('name'):
                title_parts.append(building_info['name'])
            
            title = ' - '.join(title_parts) if title_parts else "Departamento en AssetPlan"
            
            # Determinar precio
            price = None
            price_uf = None
            
            if property_data.get('discount_price'):
                price = property_data['discount_price']
                price_uf = self._parse_price_uf(price)
            elif property_data.get('original_price'):
                price = property_data['original_price'] 
                price_uf = self._parse_price_uf(price)
            elif unit_data and unit_data.get('monthly_price'):
                price = unit_data['monthly_price']
                price_uf = self._parse_price_uf(price)
            elif typology.get('price_text'):
                price = typology['price_text']
                price_uf = typology.get('price_uf')
            
            # Determinar ubicación
            location = None
            if property_data.get('address'):
                location = property_data['address']
            elif building_info.get('address'):
                location = building_info['address']
            elif building_data.get('address'):
                location = building_data['address']
            
            # Crear descripción
            description_parts = []
            if property_data.get('promotions'):
                description_parts.append("Promociones: " + ", ".join(property_data['promotions']))
            if property_data.get('common_expense'):
                description_parts.append(f"Gasto común: {property_data['common_expense']}")
            if property_data.get('guarantee'):
                description_parts.append(f"Garantía: {property_data['guarantee']}")
            if property_data.get('features'):
                description_parts.append("Características: " + ", ".join(property_data['features']))
            
            description = " | ".join(description_parts) if description_parts else None
            
            # NO agregar imágenes a propiedades individuales - solo a tipologías
            # Las imágenes de unidades individuales se recuperarán via collection.get_property_images()
            unique_images = []
            
            # Extraer ID de la URL (selectedUnit parameter)
            property_id = self._extract_property_id_from_url(current_url)
            
            # Crear property con metadatos de tipología para optimización posterior
            prop = Property(
                id=property_id,
                title=title,
                price=price,
                price_uf=price_uf,
                location=location,
                area_m2=typology.get('area_m2'),
                bedrooms=typology.get('bedrooms'),
                bathrooms=typology.get('bathrooms'),
                property_type="Departamento",
                url=self.driver.current_url,
                unit_number=unit_data.get('apartment_number') if unit_data else None,
                floor=property_data.get('floor') or (unit_data.get('floor') if unit_data else None),
                images=unique_images[:10],  # Máximo 10 imágenes
                description=description
            )
            
            logger.debug(f"✅ Propiedad creada exitosamente: {prop.title}")
            return prop, typology  # Retornar tanto la propiedad como los metadatos de tipología
            
        except Exception as e:
            logger.error(f"Error creando objeto Property: {e}")
            return None
    
    def _extract_property_id_from_url(self, url: str) -> Optional[str]:
        """Extrae el ID de la propiedad del parámetro selectedUnit en la URL."""
        try:
            if "selectedUnit=" in url:
                # Buscar el parámetro selectedUnit
                import re
                match = re.search(r'selectedUnit=(\d+)', url)
                if match:
                    property_id = match.group(1)
                    logger.debug(f"🆔 ID extraído de URL: {property_id}")
                    return property_id
                else:
                    logger.warning(f"⚠️ selectedUnit encontrado pero sin valor numérico en URL: {url}")
            else:
                logger.debug(f"⚠️ selectedUnit no encontrado en URL: {url}")
            return None
        except Exception as e:
            logger.error(f"Error extrayendo ID de URL {url}: {e}")
            return None
    
    def _extract_floor_from_page(self) -> Optional[int]:
        """Extrae el número de piso directamente de la página del departamento.
        
        Versión optimizada: solo una búsqueda rápida para evitar regresión de rendimiento.
        """
        try:
            # Solo intentar una búsqueda XPath simple y rápida
            # Buscar elementos que contengan "Piso" con timeout muy bajo
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Piso')]")
            
            if len(elements) > 10:  # Si hay demasiados elementos, saltar para evitar lentitud
                logger.debug("🏢 Demasiados elementos con 'Piso', saltando extracción por rendimiento")
                return None
            
            import re
            for element in elements[:5]:  # Máximo 5 elementos para mantener velocidad
                try:
                    text = element.text.strip()
                    if len(text) > 100:  # Saltar textos muy largos
                        continue
                        
                    match = re.search(r'Piso\s*(\d+)', text, re.IGNORECASE)
                    if match:
                        floor = int(match.group(1))
                        if 1 <= floor <= 50:
                            logger.debug(f"🏢 Piso extraído de página: {floor}")
                            return floor
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extrayendo piso de página: {e}")
            return None
    
    def _extract_floor_from_unit_number(self, unit_number: str) -> Optional[int]:
        """Extrae el número de piso del número de departamento.
        
        Ejemplos:
        - "1011-A" -> 10 (piso 10)
        - "1116-A" -> 11 (piso 11) 
        - "304-B" -> 3 (piso 3)
        - "2015" -> 20 (piso 20)
        """
        if not unit_number:
            return None
            
        try:
            import re

            # Buscar patrón de números al inicio (antes de cualquier letra o guión)
            match = re.match(r'^(\d+)', str(unit_number).strip())
            if match:
                number_part = match.group(1)
                
                # Si tiene 4 dígitos o más, tomar los primeros n-2 dígitos como piso
                if len(number_part) >= 4:
                    floor = int(number_part[:-2])  # Remover últimos 2 dígitos (número de depto)
                # Si tiene 3 dígitos, tomar el primer dígito como piso
                elif len(number_part) == 3:
                    floor = int(number_part[0])
                # Si tiene 2 dígitos o menos, no se puede determinar el piso
                else:
                    return None
                    
                # Validar que el piso sea razonable (1-50)
                if 1 <= floor <= 50:
                    logger.debug(f"🏢 Piso extraído: {floor} de unit_number: {unit_number}")
                    return floor
                else:
                    logger.debug(f"🏢 Piso {floor} fuera de rango razonable para unit_number: {unit_number}")
                    return None
            else:
                logger.debug(f"🏢 No se pudo extraer piso de unit_number: {unit_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error extrayendo piso de unit_number {unit_number}: {e}")
            return None
    
    def _parse_bedrooms(self, text: str) -> Optional[int]:
        """Parsea número de dormitorios del texto."""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*dormitorio[s]?',
            r'(\d+)\s*D',
            r'(\d+)D/\d+B'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        return None
    
    def _parse_bathrooms(self, text: str) -> Optional[int]:
        """Parsea número de baños del texto."""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*baño[s]?',
            r'(\d+)\s*B',
            r'\d+D/(\d+)B'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    continue
        return None
    
    def _parse_area(self, text: str) -> Optional[float]:
        """Parsea área en m² del texto."""
        if not text:
            return None
        
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*m[²2]',
            r'(\d+(?:[.,]\d+)?)\s*metros'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', '.'))
                except:
                    continue
        return None
    
    def _parse_price_uf(self, text: str) -> Optional[float]:
        """Parsea precio en UF del texto."""
        if not text:
            return None
        
        patterns = [
            r'UF\s*([0-9.,]+)',
            r'([0-9.,]+)\s*UF'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', '').replace('.', ''))
                except:
                    continue
        return None
    
    def _parse_units_count(self, text: str) -> int:
        """Parsea cantidad de unidades del texto."""
        if not text:
            return 0
        
        match = re.search(r'Ver\s*(\d+)', text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
        
        return 1 if 'ver' in text.lower() else 0
    
    def _handle_navigation_errors(self, error: Exception, context: str) -> bool:
        """
        Maneja errores de navegación y decide si continuar o abortar.
        
        Args:
            error: Excepción ocurrida
            context: Contexto donde ocurrió el error
            
        Returns:
            True si se puede continuar, False si se debe abortar
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Errores recuperables
        recoverable_errors = [
            "TimeoutException",
            "NoSuchElementException", 
            "StaleElementReferenceException"
        ]
        
        # Errores de red temporales
        network_errors = [
            "WebDriverException",
            "ConnectionRefusedError",
            "RemoteDisconnected"
        ]
        
        if error_type in recoverable_errors:
            logger.warning(f"Error recuperable en {context}: {error_msg}")
            return True
        elif error_type in network_errors:
            logger.warning(f"Error de red en {context}, reintentando: {error_msg}")
            self._smart_delay(2.0, 5.0)  # Delay más largo para problemas de red
            return True
        else:
            logger.error(f"Error no recuperable en {context}: {error_msg}")
            return False
    
    def _validate_building_data(self, building_data: Dict[str, Any]) -> bool:
        """
        Valida que los datos del edificio sean suficientes para continuar.
        
        Args:
            building_data: Datos del edificio a validar
            
        Returns:
            True si los datos son válidos
        """
        # Debe tener al menos ID y URL
        if not building_data.get('building_id'):
            logger.debug("Edificio rechazado: sin ID")
            return False
            
        if not building_data.get('url'):
            logger.debug("Edificio rechazado: sin URL")
            return False
            
        # URL debe ser válida
        url = building_data.get('url', '')
        if not url or 'assetplan.cl' not in url or '/edificio/' not in url:
            logger.debug(f"Edificio rechazado: URL inválida: {url}")
            return False
            
        return True
    
    def _extract_properties_alternative_method(self, max_properties: int) -> List[Property]:
        """
        Método alternativo de extracción cuando no se encuentran building cards.
        Busca directamente enlaces de departamentos.
        """
        logger.info("Usando método alternativo de extracción")
        properties = []
        
        try:
            # Buscar enlaces directos a departamentos
            department_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/arriendo/departamento/']")
            logger.info(f"Encontrados {len(department_links)} enlaces directos de departamentos")
            
            for i, link in enumerate(department_links[:max_properties]):
                try:
                    href = link.get_attribute('href')
                    if href and self._is_valid_department_url(href):
                        # Navegar al departamento
                        self.driver.get(href)
                        self._smart_delay(1.5, 2.5)
                        
                        # Extraer datos
                        property_data = self._extract_department_detail_page()
                        
                        # Crear property básica
                        prop = self._create_basic_property_from_url(href, property_data)
                        if prop:
                            properties.append(prop)
                            logger.debug(f"Extraída propiedad {i+1}: {prop.title}")
                        
                        # Delay entre propiedades
                        self._smart_delay(1.0, 2.0)
                        
                except Exception as e:
                    logger.debug(f"Error procesando enlace alternativo: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error en método alternativo: {e}")
        
        return properties
    
    def _is_valid_department_url(self, url: str) -> bool:
        """Verifica si la URL es válida para un departamento."""
        if not url:
            return False
        
        # Debe contener coordenadas y ser de AssetPlan
        return ('/arriendo/departamento/' in url and 
                'assetplan.cl' in url and
                any(coord in url for coord in ['-70.', '-33.']))
    
    def _create_basic_property_from_url(self, url: str, property_data: Dict[str, Any]) -> Optional[Property]:
        """Crea una Property básica a partir de URL y datos extraídos."""
        try:
            title = property_data.get('community_name', 'Departamento AssetPlan')
            if property_data.get('apartment_number'):
                title += f" - Depto {property_data['apartment_number']}"
            
            # Precio
            price = property_data.get('discount_price') or property_data.get('original_price')
            price_uf = self._parse_price_uf(price) if price else None
            
            return Property(
                title=title,
                price=price,
                price_uf=price_uf,
                location=property_data.get('address'),
                property_type="Departamento",
                url=url,
                images=property_data.get('image_urls', [])[:5],
                description=f"Promociones: {', '.join(property_data.get('promotions', []))}" if property_data.get('promotions') else None
            )
            
        except Exception as e:
            logger.error(f"Error creando property básica: {e}")
            return None
    
    def _generate_typology_id(self, typology_data: Dict[str, Any]) -> str:
        """Genera un ID único para una tipología basado en sus características."""
        # Usar características únicas de la tipología
        key_parts = []
        
        if typology_data.get('bedrooms') is not None:
            key_parts.append(f"bed{typology_data['bedrooms']}")
        if typology_data.get('bathrooms') is not None:
            key_parts.append(f"bath{typology_data['bathrooms']}")
        if typology_data.get('area_m2') is not None:
            key_parts.append(f"area{int(typology_data['area_m2'])}")
        if typology_data.get('rooms_info'):
            # Limpiar y usar info de habitaciones
            clean_info = typology_data['rooms_info'].replace(' ', '').replace('+', '').replace('\n', '').lower()
            key_parts.append(clean_info[:10])  # Primeros 10 caracteres
        
        # Si no hay suficientes datos, usar la URL de la tipología
        if not key_parts and typology_data.get('units_url'):
            import hashlib
            url_hash = hashlib.md5(typology_data['units_url'].encode()).hexdigest()[:8]
            key_parts.append(f"url{url_hash}")
        
        # Fallback si no hay datos
        if not key_parts:
            key_parts.append("unknown")
        
        return "_".join(key_parts)
    
    
    def _extract_typology_images_with_building(self, typology_data: Dict[str, Any], 
                                             building_info: Dict[str, Any], 
                                             building_data: Dict[str, Any]) -> List[str]:
        """Extrae imágenes de tipología + edificio (compartidas por todas las unidades de la tipología)."""
        images = []
        
        # 1. Imágenes específicas de la tipología
        if typology_data.get('image_url'):
            images.append(typology_data['image_url'])
        
        if typology_data.get('gallery_urls'):
            images.extend(typology_data['gallery_urls'])
        
        # 2. Imágenes del edificio (compartidas por todas las tipologías)
        if building_data.get('image_url'):
            images.append(building_data['image_url'])
        
        if building_info.get('gallery_urls'):
            images.extend(building_info['gallery_urls'])
        
        # Remover duplicados manteniendo orden
        seen = set()
        unique_images = []
        for img in images:
            if img and img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        return unique_images
    
    
    def _extract_from_multiple_buildings(self, building_cards: List[Dict], 
                                       max_properties: int, max_typologies: int) -> List[Property]:
        """
        Extrae propiedades de múltiples edificios usando navegación back para saltar entre ellos.
        
        Flujo:
        1. Procesar edificio 1 -> extraer N propiedades 
        2. Back x2 para volver a lista de edificios
        3. Procesar edificio 2 -> extraer M propiedades
        4. Repetir hasta max_typologies edificios o max_properties total
        
        Args:
            building_cards: Lista de datos de edificios
            max_properties: Máximo total de propiedades
            max_typologies: Máximo número de edificios/tipologías a procesar
            
        Returns:
            Lista de propiedades extraídas de múltiples edificios
        """
        if not self.extreme_mode:
            logger.info(f"🏢 MULTI-TIPOLOGÍA: {max_typologies} edificios, {max_properties} props max")
        else:
            logger.info(f"⚡ MULTI: {max_typologies} edificios")
        
        all_properties = []
        processed_buildings = 0
        properties_per_building = max(1, max_properties // max_typologies)  # Distribuir props entre edificios
        
        # Lista de edificios a procesar (limitada por max_typologies)
        buildings_to_process = building_cards[:max_typologies]
        
        for building_index, building_data in enumerate(buildings_to_process):
            if len(all_properties) >= max_properties:
                break
                
            try:
                # Validar edificio
                if not self._validate_building_data(building_data):
                    logger.debug(f"Edificio {building_data.get('name', 'unknown')} no pasó validación")
                    continue
                
                # Calcular cuántas propiedades extraer de este edificio
                remaining_props = max_properties - len(all_properties)
                remaining_buildings = len(buildings_to_process) - building_index
                props_for_this_building = min(properties_per_building, remaining_props, 
                                            max(1, remaining_props // remaining_buildings))
                
                if not self.extreme_mode:
                    logger.info(f"🏠 Procesando edificio {processed_buildings + 1}/{max_typologies}: "
                              f"{building_data.get('name', 'unknown')} (hasta {props_for_this_building} props)")
                
                # PASO 1: Procesar edificio actual
                building_properties = self._process_building(building_data, props_for_this_building)
                
                # Añadir propiedades respetando el límite máximo
                remaining_space = max_properties - len(all_properties)
                if remaining_space > 0:
                    properties_to_add = building_properties[:remaining_space]
                    all_properties.extend(properties_to_add)
                
                processed_buildings += 1
                
                if not self.extreme_mode:
                    logger.info(f"✅ Edificio {processed_buildings}: +{len(building_properties)} "
                              f"(Total: {len(all_properties)}/{max_properties})")
                
                # PASO 2: Navegación back para próximo edificio (si no es el último)
                if building_index < len(buildings_to_process) - 1:
                    if not self._navigate_back_to_buildings_list():
                        logger.warning(f"No se pudo navegar back a lista de edificios, deteniendo multi-tipología")
                        break
                    
                    # Delay entre edificios
                    self._smart_delay(1.5, 3.0)
                
            except Exception as e:
                logger.error(f"Error procesando edificio {building_data.get('name', 'unknown')}: {e}")
                
                # Intentar recuperación navegando back
                try:
                    if building_index < len(buildings_to_process) - 1:
                        self._navigate_back_to_buildings_list()
                        self._smart_delay(2.0, 4.0)
                except:
                    logger.error("Error en recuperación, deteniendo extracción multi-tipología")
                    break
        
        if not self.extreme_mode:
            logger.info(f"🎯 MULTI-TIPOLOGÍA completado: {len(all_properties)} props de {processed_buildings} edificios")
        else:
            logger.info(f"⚡ MULTI FIN: {len(all_properties)} props")
        
        return all_properties
    
    def _navigate_back_to_buildings_list(self) -> bool:
        """
        Navega de vuelta a la lista de edificios usando navegación back.
        
        Flujo esperado:
        - Desde página de departamento -> back -> página de edificio  
        - Desde página de edificio -> back -> lista de edificios
        
        Returns:
            True si la navegación fue exitosa, False si falló
        """
        try:
            current_url_before = self.driver.current_url
            
            if not self.extreme_mode:
                logger.debug(f"🔙 Navegando back desde: {current_url_before}")
            
            # BACK #1: De página de departamento a página de edificio  
            self._smart_back_to_modal()
            self._smart_delay(1.0, 2.0)
            
            current_url_after_first_back = self.driver.current_url
            
            # BACK #2: De página de edificio a lista de edificios
            self.driver.back()
            self.wait.until(lambda d: d.current_url != current_url_after_first_back)
            self._smart_delay(1.0, 2.0)
            
            final_url = self.driver.current_url
            
            # Verificar que llegamos a una página de búsqueda/lista
            if ("/arriendo/departamento" in final_url and 
                ("page=" in final_url or final_url.endswith("/departamento"))):
                
                if not self.extreme_mode:
                    logger.debug(f"✅ Back exitoso a: {final_url}")
                return True
            else:
                logger.warning(f"Back no llegó a lista de edificios. URL final: {final_url}")
                return False
                
        except Exception as e:
            logger.error(f"Error navegando back a lista de edificios: {e}")
            return False