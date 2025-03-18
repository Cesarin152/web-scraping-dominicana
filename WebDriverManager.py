import logging
import platform
import os

from selenium import webdriver
from selenium.common.exceptions import (
    SessionNotCreatedException,
    WebDriverException
)

# Para Edge
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions

# Para Chrome/Chromium
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

# Para Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions


class WebDriverManager:
    """
    Clase para la gestión de distintos navegadores con Selenium WebDriver.
    Ofrece métodos para inicializar y cerrar el driver, así como un 
    context manager opcional para manejar automáticamente su ciclo de vida.

    Atributos:
    -----------
    browser : str
        Nombre del navegador a usar ("edge", "chrome", "firefox").
    headless : bool
        Define si el navegador se ejecutará en modo headless (sin interfaz).
    driver_path : str | None
        Ruta al driver específico, en caso de no usar el instalado por defecto.
    driver : WebDriver | None
        Instancia del WebDriver.
    """

    def __init__(
        self,
        browser: str = "edge",
        headless: bool = True,
        driver_path: str = None
    ):
        self.browser = browser.lower().strip()
        self.headless = headless
        self.driver_path = driver_path
        self.driver = None

        # Determinar si estamos en Jetson Nano (arquitectura aarch64)
        self._is_jetson = (platform.machine() == "aarch64")

    def init_driver(self):
        """
        Inicializa el WebDriver según los parámetros de configuración (browser, headless, driver_path).
        Retorna:
            WebDriver: instancia creada del driver.
        """
        logging.info(f"Inicializando WebDriver para navegador '{self.browser}'...")
        try:
            self.driver = self._create_driver()
            return self.driver
        except SessionNotCreatedException:
            logging.error("Error: Sesión no creada. "
                          "Revisa la versión del driver o la instalación.", exc_info=True)
            raise
        except WebDriverException:
            logging.error("Error al inicializar el WebDriver. "
                          "Revisa la compatibilidad o configuración.", exc_info=True)
            raise
        except Exception:
            logging.error("Error inesperado al inicializar el WebDriver.", exc_info=True)
            raise

    def _create_driver(self):
        """
        Método interno que actúa como factory para crear el driver
        dependiendo del navegador solicitado.
        Aplica ajustes adicionales si se detecta Jetson (aarch64) o Ubuntu.
        """

        # === Caso: Microsoft Edge ===
        if self.browser == "edge":
            if self._is_jetson:
                # Edge en Jetson no está soportado oficialmente.
                logging.warning("Edge no está soportado oficialmente en NVIDIA Jetson. "
                                "Podrías probar 'chrome' o 'firefox'.")

            options = EdgeOptions()

            if self.headless:
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")

            # Ajustes recomendados en entornos Jetson
            if self._is_jetson:
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            # Crear Service
            service = self._create_edge_service()

            return webdriver.Edge(service=service, options=options)

        # === Caso: Google Chrome / Chromium ===
        elif self.browser == "chrome":
            options = ChromeOptions()

            if self.headless:
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")

            # Ajustes recomendados para Jetson
            if self._is_jetson:
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            # Crear Service
            service = self._create_chrome_service()

            return webdriver.Chrome(service=service, options=options)

        # === Caso: Mozilla Firefox ===
        elif self.browser == "firefox":
            options = FirefoxOptions()

            # Modo headless
            if self.headless:
                options.headless = True

            # Crear Service
            service = self._create_firefox_service()

            return webdriver.Firefox(service=service, options=options)

        # === Caso: navegador no soportado ===
        else:
            raise ValueError(
                f"Navegador '{self.browser}' no soportado. "
                "Opciones válidas: 'edge', 'chrome', 'firefox'."
            )

    def _create_edge_service(self):
        """
        Crea el objeto Service para Microsoft Edge.
        """
        if self.driver_path:
            return EdgeService(executable_path=self.driver_path)
        # Asume que el path está en el PATH del sistema (p.e. /usr/bin)
        return EdgeService()

    def _create_chrome_service(self):
        """
        Crea el objeto Service para Chrome/Chromium.
        Si estamos en Jetson y no se especificó driver_path, se
        busca en rutas típicas (/usr/bin/chromedriver, etc.).
        """
        driver_path = self.driver_path

        if not driver_path and self._is_jetson:
            possible_paths = ["/usr/bin/chromedriver", "/usr/local/bin/chromedriver"]
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    driver_path = path
                    break

        if driver_path:
            return ChromeService(executable_path=driver_path)
        return ChromeService()

    def _create_firefox_service(self):
        """
        Crea el objeto Service para Firefox/GeckoDriver.
        Si estamos en Jetson y no se especificó driver_path, 
        se busca en rutas típicas (/usr/bin/geckodriver, etc.).
        """
        driver_path = self.driver_path

        if not driver_path and self._is_jetson:
            possible_paths = ["/usr/bin/geckodriver", "/usr/local/bin/geckodriver"]
            for path in possible_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    driver_path = path
                    break

        if driver_path:
            return FirefoxService(executable_path=driver_path)
        return FirefoxService()

    def close_driver(self):
        """
        Cierra la instancia del WebDriver si está activa.
        """
        if self.driver:
            logging.info("Cerrando WebDriver...")
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        """
        Permite usar WebDriverManager con la sintaxis 'with'. 
        Retorna la instancia de driver.
        """
        self.init_driver()
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Cierra el driver automáticamente al salir del bloque 'with'.
        """
        self.close_driver()
