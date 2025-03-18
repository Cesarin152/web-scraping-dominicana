import os
import time
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from Utilities import FileManagerUtil


class DownloadConfig:
    """
    Clase que contiene la configuración para el proceso de descarga.
    """
    def __init__(
        self,
        table_check_xpath: str,
        download_button_xpath: str,
        default_filename: str = "QuickAnalysis.xlsx",
        renamed_filename_pattern: str = "QuickAnalysis_{day}_{month}_{year}.xlsx",
        download_directory: str = None,
        wait_time: int = 30,
        max_download_wait: int = 60
    ):
        """
        Parámetros:
        -----------
        table_check_xpath : str
            XPATH de un elemento que indica que la tabla está presente y lista
            (por ejemplo, un botón o columna).
        download_button_xpath : str
            XPATH del botón para iniciar la descarga.
        default_filename : str
            Nombre de archivo por defecto que se descarga (antes de renombrar).
        renamed_filename_pattern : str
            Patrón para renombrar el archivo una vez descargado.
            Puede incluir {day}, {month}, {year} que se reemplazan dinámicamente.
        download_directory : str
            Directorio donde se guardan las descargas. Si es None,
            se asume la carpeta de descargas del usuario.
        wait_time : int
            Tiempo de espera por defecto para `WebDriverWait` en esta clase.
        max_download_wait : int
            Tiempo máximo (segundos) para esperar a que el archivo aparezca tras pulsar descargar.
        """
        self.table_check_xpath = table_check_xpath
        self.download_button_xpath = download_button_xpath
        self.default_filename = default_filename
        self.renamed_filename_pattern = renamed_filename_pattern
        self.download_directory = download_directory
        self.wait_time = wait_time
        self.max_download_wait = max_download_wait


class DownloadService:
    """
    Servicio para gestionar la descarga de datos desde una página web:
    1. Esperar a que la tabla o botón de descarga esté listo.
    2. Pulsar el botón de descarga.
    3. Esperar a que el archivo aparezca en disco.
    4. Renombrar el archivo usando un patrón configurable.
    """

    def __init__(self, driver, config: DownloadConfig):
        """
        Parámetros:
        -----------
        driver : WebDriver
            Instancia de Selenium WebDriver inicializada.
        config : DownloadConfig
            Configuración de descargas (XPaths, nombre de archivo, etc.).
        """
        self.driver = driver
        self.config = config

    def download_data(self, day: str = None, month: str = None, year: str = None):
        """
        Ejecuta el proceso de descarga y renombrado.
        Parámetros:
        -----------
        day : str | None
            Día para el nombre del archivo renombrado. Si None, se toma el actual.
        month : str | None
            Mes para el nombre del archivo renombrado. Si None, se toma el actual.
        year : str | None
            Año para el nombre del archivo renombrado. Si None, se toma el actual.
        """
        try:
            logging.info("Iniciando descarga de datos...")

            wait = WebDriverWait(self.driver, self.config.wait_time)

            # Asegurarnos de que la tabla o el botón de descarga se haya cargado:
            wait.until(EC.presence_of_element_located((By.XPATH, self.config.table_check_xpath)))

            # Pulsar el botón de descarga
            download_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, self.config.download_button_xpath))
            )
            self.checked_click(download_button)
            logging.info("Botón de descarga pulsado. Esperando aparición del archivo en disco...")

            # Esperar a que el archivo aparezca en la carpeta de descargas
            downloaded_file = self._wait_for_downloaded_file(
                filename=self.config.default_filename,
                timeout=self.config.max_download_wait
            )
            if not downloaded_file:
                raise FileNotFoundError(f"No se encontró el archivo '{self.config.default_filename}' "
                                        f"en el tiempo máximo de {self.config.max_download_wait}s.")

            # Renombrar el archivo descargado
            final_name = self._generate_filename(day, month, year)
            FileManagerUtil.rename_file(downloaded_file, final_name, self.config.download_directory)

            logging.info(f"Descarga y renombrado completado. Archivo final: {final_name}")
        except Exception as e:
            logging.error("Error en download_data.", exc_info=True)
            raise

    def checked_click(self, element):
        """
        Hace click en el elemento si no está seleccionado o si no es un checkbox.
        """
        try:
            # Para checkboxes: sólo hace click si no está seleccionado.
            if hasattr(element, 'is_selected') and element.is_selected():
                return
            element.click()
        except Exception as e:
            logging.error("Error al hacer click en el elemento de descarga.", exc_info=True)
            raise

    def _wait_for_downloaded_file(self, filename: str, timeout: int) -> str:
        """
        Espera hasta que aparezca un archivo con el nombre `filename` en el
        directorio de descargas. Retorna la ruta completa del archivo si se
        encuentra dentro del tiempo límite, o None si no aparece.
        """
        download_dir = self.config.download_directory
        if not download_dir:
            # Tomar carpeta de descargas por defecto del usuario
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')

        full_path = os.path.join(download_dir, filename)

        elapsed = 0
        interval = 1  # segundos
        while elapsed < timeout:
            if os.path.exists(full_path):
                # Verificamos si el archivo está siendo escrito (opcional)
                # Para ello, podemos intentar abrirlo en modo append.
                try:
                    with open(full_path, 'ab'):
                        pass
                    return full_path
                except PermissionError:
                    # Archivo aún en proceso de descarga
                    time.sleep(interval)
                    elapsed += interval
            else:
                time.sleep(interval)
                elapsed += interval

        return None  # No se encontró en el tiempo limite

    def _generate_filename(self, day: str, month: str, year: str) -> str:
        """
        Genera el nombre final del archivo usando el patrón en config. Si
        day/month/year no se pasan, se usan valores actuales de time.strftime().
        """
        day = day or time.strftime("%d")
        month = month or time.strftime("%B")
        year = year or time.strftime("%Y")

        # Reemplazar placeholders en el patrón
        final_name = self.config.renamed_filename_pattern.format(
            day=day, month=month, year=year
        )
        return final_name
