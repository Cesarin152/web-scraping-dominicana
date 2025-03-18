import logging
import time
import pandas as pd
import matplotlib
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from Utilities import DatePickerUtil


class DataSelectionConfig:
    """
    Clase que contiene la configuración relevante para la selección de datos:
    - URL de la página donde se hace la selección (url_analysis).
    - XPaths de los elementos clave (botón diario, botón siguiente, tabla, etc.).
    """
    def __init__(
        self,
        url_analysis: str,
        daily_button_xpath: str,
        date_picker_xpath: str,
        typology_select_xpath: str,
        next_button_xpath: str,
        confirm_button_xpath: str,
        table_xpath: str,
        pagination_next_xpath: str
    ):
        self.url_analysis = url_analysis
        self.daily_button_xpath = daily_button_xpath
        self.date_picker_xpath = date_picker_xpath  # Opcional si quisieras localizar el datepicker
        self.typology_select_xpath = typology_select_xpath
        self.next_button_xpath = next_button_xpath
        self.confirm_button_xpath = confirm_button_xpath
        self.table_xpath = table_xpath
        self.pagination_next_xpath = pagination_next_xpath


class DataSelectionService:
    """
    Servicio para:
    1. Acceder a la url de análisis.
    2. Seleccionar la vista diaria (u otra).
    3. Elegir la fecha (day, month, year).
    4. Seleccionar la tipología, elementos y parámetros.
    5. Extraer una tabla paginada y guardarla en CSV (si se requiere).

    Parámetros:
    -----------
    driver : WebDriver
        Instancia inicializada de Selenium WebDriver
    config : DataSelectionConfig
        Objeto con los XPaths y la URL de análisis
    typology_dict : dict
        Diccionario que mapea la 'typology' a sus XPaths (ver 'Typology.Typology' original)
    wait_time : int
        Tiempo máximo de espera por defecto para WebDriverWait
    day : int
        Día a seleccionar
    month : str
        Mes a seleccionar (por ejemplo "febrero")
    year : int
        Año a seleccionar
    elements : list[str]
        Lista de elementos a marcar
    parameters : list[str]
        Lista de parámetros a marcar
    typology_key : str
        La clave de tipología, p.ej. "Inversor - (INVERSOR)"
    """

    def __init__(
        self,
        driver,
        config: DataSelectionConfig,
        typology_dict: dict,
        wait_time: int = 10,
        day: int = 1,
        month: str = "febrero",
        year: int = 2025,
        elements: list[str] = None,
        parameters: list[str] = None,
        typology_key: str = "Inversor - (INVERSOR)"
    ):
        self.driver = driver
        self.config = config
        self.typology_dict = typology_dict
        self.wait_time = wait_time
        self.day = day
        self.month = month
        self.year = year
        self.elements = elements or []
        self.parameters = parameters or []
        self.typology_key = typology_key

    def select_data(self):
        """
        Selecciona la vista diaria, la fecha, la tipología,
        los elementos y los parámetros configurados.
        Luego, puede extraer la tabla resultante.
        """
        try:
            logging.info("Navegando a la página de análisis...")
            self.driver.get(self.config.url_analysis)

            wait = WebDriverWait(self.driver, self.wait_time)

            # Seleccionar botón para visualizar datos diarios
            logging.info("Seleccionando vista diaria...")
            day_button = wait.until(EC.element_to_be_clickable((By.XPATH, self.config.daily_button_xpath)))
            self.checked_click(day_button)

            # Seleccionar la fecha con el utilitario
            logging.info(f"Seleccionando la fecha: {self.day}-{self.month}-{self.year}")
            DatePickerUtil.select_date(self.driver, self.day, self.month, self.year)
            # Puede que se requiera un sleep
            # Pendiente: se usaría WebDriverWait con alguna condición que indique que la tabla se refrescó.
            time.sleep(2)

            # Seleccionar tipología
            logging.info(f"Seleccionando tipología: {self.typology_key}")
            typology_element = wait.until(
                EC.presence_of_element_located((By.XPATH, self.config.typology_select_xpath))
            )
            select_typology = Select(typology_element)
            select_typology.select_by_visible_text(self.typology_key)

            # Esperar a que se actualice la página
            # Pendiente: Cambiar a un "wait_for_page_loaded"
            time.sleep(2)

            # Seleccionar elementos
            self._select_elements(wait)

            # Seleccionar parámetros
            self._select_parameters(wait)

            # Botón siguiente (OK)
            logging.info("Pulsando botón 'OK' para continuar...")
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, self.config.next_button_xpath)))
            self.checked_click(next_button)
            time.sleep(2)

            #Extraer la tabla resultante
            self._extract_table(wait, self.config.table_xpath, self.config.pagination_next_xpath)

            # Confirmar datos
            try:
                confirm_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, self.config.confirm_button_xpath))
                )
                self.checked_click(confirm_button)
            except Exception:
                logging.info("No se encontró el último botón de confirmación, saltando paso...")

            logging.info("Selección de datos completada.")
        except Exception as e:
            logging.error("Error en select_data.", exc_info=True)
            raise

    def _select_elements(self, wait: WebDriverWait):
        """
        Marca los checkboxes correspondientes a los 'elements' configurados,
        usando el diccionario 'Typology' para resolver el XPATH.
        """
        if not self.elements:
            return
        for element_name in self.elements:
            xpath = self.typology_dict[self.typology_key]['Elements'].get(element_name)
            if not xpath:
                logging.warning(f"No se encontró el XPATH para el elemento '{element_name}'.")
                continue
            elem_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.checked_click(elem_checkbox)
            time.sleep(0.5)  # Pequeña pausa para permitir que la interfaz se actualice

    def _select_parameters(self, wait: WebDriverWait):
        """
        Marca los checkboxes correspondientes a los 'parameters' configurados,
        usando el diccionario 'Typology' para resolver el XPATH.
        """
        if not self.parameters:
            return
        for param_name in self.parameters:
            xpath = self.typology_dict[self.typology_key]['Parameters'].get(param_name)
            if not xpath:
                logging.warning(f"No se encontró el XPATH para el parámetro '{param_name}'.")
                continue
            param_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            self.checked_click(param_checkbox)
            time.sleep(0.5)

    def _extract_table(self, wait: WebDriverWait, pagination_next_xpath: str, table_xpath ='//table[contains(@class, "table")]'):
        """
        Extrae la tabla paginada y la guarda en CSV.
        Este método se puede separar en otra clase si lo deseas.
        """
        logging.info("Iniciando extracción de tabla...")
        data = []

        # Esperar a que aparezca la tabla
        table_element = wait.until(EC.presence_of_element_located((By.XPATH, table_xpath)))

        # Se obtienen los headers
        header_elements = table_element.find_elements(By.XPATH, './/thead//th')
        headers = [header.text.strip() for header in header_elements if header.text.strip()]

        while True:
            # Re-obtener la tabla en cada página para asegurarse de que los elementos se actualicen
            table_element = wait.until(EC.presence_of_element_located((By.XPATH, table_xpath)))
            rows = table_element.find_elements(By.XPATH, './/tbody/tr')

            for row in rows:
                cells = row.find_elements(By.XPATH, './td')
                values = [cell.text.strip() for cell in cells]
                data.append(values)

            # Intentar pulsar el botón de siguiente en la paginación
            try:
                next_button = self.driver.find_element(By.XPATH, pagination_next_xpath)
                # Verificar si está inhabilitado o no. Asumiendo que se usa la clase "disabled" o similar
                if 'disabled' in next_button.get_attribute('class'):
                    break  # No hay más páginas
                self.checked_click(next_button)
                # Esperar a que la nueva página se cargue
                time.sleep(1)
            except Exception:
                # Si no existe el botón o no es clickable, se asume fin de paginación
                break

        # Guardar en CSV
        df = pd.DataFrame(data, columns=headers if headers else None)
        file_name = f"Data_{self.typology_key}_{self.day}_{self.month}_{self.year}.xlsx"
        df.to_excel(file_name, index=False)
        logging.info(f"Tabla extraída y guardada en: {file_name}")

    def checked_click(self, element):
        """
        Hace click en un checkbox o botón solo si no está ya seleccionado.
        """
        # Para checkboxes: si no está seleccionado, haz click.
        # Para botones: normalmente no tienen "is_selected", se puede hacer click directo
        try:
            if hasattr(element, 'is_selected') and element.is_selected():
                return
            element.click()
        except Exception as e:
            logging.error("Error al hacer click en el elemento.", exc_info=True)
            raise


class Parameters:
    Parameters_inv = {
        "CALIDAD COM": '//*[@id="quick-analysis"]//span[contains(text(),"CALIDAD COM")]/parent::label',
        "CORRIENTE AC FASE 1": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE AC FASE 1")]/parent::label',
        "CORRIENTE AC FASE 2": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE AC FASE 2")]/parent::label',
        "CORRIENTE AC FASE 3": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE AC FASE 3")]/parent::label',
        "CORRIENTE DC": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC")]/parent::label',
        "CORRIENTE DC IN 01": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 01")]/parent::label',
        "CORRIENTE DC IN 02": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 02")]/parent::label',
        "CORRIENTE DC IN 03": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 03")]/parent::label',
        "CORRIENTE DC IN 04": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 04")]/parent::label',
        "CORRIENTE DC IN 05": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 05")]/parent::label',
        "CORRIENTE DC IN 06": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 06")]/parent::label',
        "CORRIENTE DC IN 07": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 07")]/parent::label',
        "CORRIENTE DC IN 08": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 08")]/parent::label',
        "CORRIENTE DC IN 09": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 09")]/parent::label',
        "CORRIENTE DC IN 10": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 10")]/parent::label',
        "CORRIENTE DC IN 11": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 11")]/parent::label',
        "CORRIENTE DC IN 12": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 12")]/parent::label',
        "CORRIENTE DC IN 13": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 13")]/parent::label',
        "CORRIENTE DC IN 14": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 14")]/parent::label',
        "CORRIENTE DC IN 15": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 15")]/parent::label',
        "CORRIENTE DC IN 16": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 16")]/parent::label',
        "CORRIENTE DC IN 17": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 17")]/parent::label',
        "CORRIENTE DC IN 18": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 18")]/parent::label',
        "CORRIENTE DC IN 19": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 19")]/parent::label',
        "CORRIENTE DC IN 20": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 20")]/parent::label',
        "CORRIENTE DC IN 21": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 21")]/parent::label',
        "CORRIENTE DC IN 22": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 22")]/parent::label',
        "CORRIENTE DC IN 23": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 23")]/parent::label',
        "CORRIENTE DC IN 24": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 24")]/parent::label',
        "CORRIENTE DC IN 25": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 25")]/parent::label',
        "CORRIENTE DC IN 26": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 26")]/parent::label',
        "CORRIENTE DC IN 27": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 27")]/parent::label',
        "CORRIENTE DC IN 28": '//*[@id="quick-analysis"]//span[contains(text(),"CORRIENTE DC IN 28")]/parent::label',
 
        "DURACION ULTIMO MUESTREO": '//*[@id="quick-analysis"]//span[contains(text(),"DURACION ULTIMO MUESTREO")]/parent::label',
        "EFICIENCIA": '//*[@id="quick-analysis"]//span[contains(text(),"EFICIENCIA")]/parent::label',
        "ENERGIA ACTIVA": '//*[@id="quick-analysis"]//span[contains(text(),"ENERGIA ACTIVA")]/parent::label',
        "ENERGIA ACTIVA AÑO": '//*[@id="quick-analysis"]//span[contains(text(),"ENERGIA ACTIVA AÑO")]/parent::label',
        "ENERGIA ACTIVA DIA": '//*[@id="quick-analysis"]//span[contains(text(),"ENERGIA ACTIVA DIA")]/parent::label',
        "ENERGIA ACTIVA MES": '//*[@id="quick-analysis"]//span[contains(text(),"ENERGIA ACTIVA MES")]/parent::label',
        "ESTADO COM": '//*[@id="quick-analysis"]//span[contains(text(),"ESTADO COM")]/parent::label',
        "FACTOR DE POTENCIA": '//*[@id="quick-analysis"]//span[contains(text(),"FACTOR DE POTENCIA")]/parent::label',
        "FECHA": '//*[@id="quick-analysis"]//span[contains(text(),"FECHA")]/parent::label',
        "FECHA ULTIMA LECTURA": '//*[@id="quick-analysis"]//span[contains(text(),"FECHA ULTIMA LECTURA")]/parent::label',
        "FRECUENCIA": '//*[@id="quick-analysis"]//span[contains(text(),"FRECUENCIA")]/parent::label',
        "HUAWEI SMARTLOGGER AJUSTE ACTIVO": '//*[@id="quick-analysis"]//span[contains(text(),"HUAWEI SMARTLOGGER AJUSTE ACTIVO")]/parent::label',
        "HUAWEI SMARTLOGGER CAPACIDAD NOMINAL PLANTA": '//*[@id="quick-analysis"]//span[contains(text(),"HUAWEI SMARTLOGGER CAPACIDAD NOMINAL PLANTA")]/parent::label',
        "HUAWEI SMARTLOGGER ESTADO COMUNICACIONES": '//*[@id="quick-analysis"]//span[contains(text(),"HUAWEI SMARTLOGGER ESTADO COMUNICACIONES")]/parent::label',
        "HUAWEI SUN2000 ESTADO": '//*[@id="quick-analysis"]//span[contains(text(),"HUAWEI SUN2000 ESTADO")]/parent::label',
        "HUAWEI SUN2000 TELEINDICACION": '//*[@id="quick-analysis"]//span[contains(text(),"HUAWEI SUN2000 TELEINDICACION")]/parent::label',
        "MARCA": '//*[@id="quick-analysis"]//span[contains(text(),"MARCA")]/parent::label',
        "MODELO": '//*[@id="quick-analysis"]//span[contains(text(),"MODELO")]/parent::label',
        "POTENCIA ACTIVA": '//*[@id="quick-analysis"]//span[text()="                                POTENCIA ACTIVA                            "]/parent::label',
        "POTENCIA DC": '//*[@id="quick-analysis"]//span[contains(text(),"POTENCIA DC")]/parent::label',
        "POTENCIA NOMINAL": '//*[@id="quick-analysis"]//span[contains(text(),"POTENCIA NOMINAL")]/parent::label',
        "RESISTENCIA AISLAMIENTO": '//*[@id="quick-analysis"]//span[contains(text(),"RESISTENCIA AISLAMIENTO")]/parent::label',
        "SETPOINT FACTOR DE POTENCIA": '//*[@id="quick-analysis"]//span[contains(text(),"SETPOINT FACTOR DE POTENCIA")]/parent::label',
        "TEMPERATURA INT": '//*[@id="quick-analysis"]//span[contains(text(),"TEMPERATURA INT")]/parent::label',
        "TENSIÓN AC FASE 1-2": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN AC FASE 1-2")]/parent::label',
        "TENSIÓN AC FASE 1-N": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN AC FASE 1-N")]/parent::label',
        "TENSIÓN AC FASE 2-3": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN AC FASE 2-3")]/parent::label',
        "TENSIÓN AC FASE 2-N": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN AC FASE 2-N")]/parent::label',
        "TENSIÓN AC FASE 3-1": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN AC FASE 3-1")]/parent::label',
        "TENSIÓN AC FASE 3-N": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN AC FASE 3-N")]/parent::label',
        "TENSIÓN DC IN 01": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 01")]/parent::label',
        "TENSIÓN DC IN 02": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 02")]/parent::label',
        "TENSIÓN DC IN 03": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 03")]/parent::label',
        "TENSIÓN DC IN 04": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 04")]/parent::label',
        "TENSIÓN DC IN 05": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 05")]/parent::label',
        "TENSIÓN DC IN 06": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 06")]/parent::label',
        "TENSIÓN DC IN 07": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 07")]/parent::label',
        "TENSIÓN DC IN 08": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 08")]/parent::label',
        "TENSIÓN DC IN 09": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 09")]/parent::label',
        "TENSIÓN DC IN 10": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 10")]/parent::label',
        "TENSIÓN DC IN 11": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 11")]/parent::label',
        "TENSIÓN DC IN 12": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 12")]/parent::label',
        "TENSIÓN DC IN 13": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 13")]/parent::label',
        "TENSIÓN DC IN 14": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 14")]/parent::label',
        "TENSIÓN DC IN 15": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 15")]/parent::label',
        "TENSIÓN DC IN 16": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 16")]/parent::label',
        "TENSIÓN DC IN 17": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 17")]/parent::label',
        "TENSIÓN DC IN 18": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 18")]/parent::label',
        "TENSIÓN DC IN 19": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 19")]/parent::label',
        "TENSIÓN DC IN 20": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 20")]/parent::label',
        "TENSIÓN DC IN 21": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 21")]/parent::label',
        "TENSIÓN DC IN 22": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 22")]/parent::label',
        "TENSIÓN DC IN 23": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 23")]/parent::label',
        "TENSIÓN DC IN 24": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 24")]/parent::label',
        "TENSIÓN DC IN 25": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 25")]/parent::label',
        "TENSIÓN DC IN 26": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 26")]/parent::label',
        "TENSIÓN DC IN 27": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 27")]/parent::label',
        "TENSIÓN DC IN 28": '//*[@id="quick-analysis"]//span[contains(text(),"TENSIÓN DC IN 28")]/parent::label'
    }
    Parameters_meteo = {
        "PYRANOMETER 1 IRRADIANCE": '//*[@id="quick-analysis"]//span[contains(text(),"PYRANOMETER 1 IRRADIANCE")]/parent::label',
        "PYRANOMETER 2 IRRADIANCE": '//*[@id="quick-analysis"]//span[contains(text(),"PYRANOMETER 2 IRRADIANCE")]/parent::label',
        "PYRANOMETER 3 IRRADIANCE": '//*[@id="quick-analysis"]//span[contains(text(),"PYRANOMETER 3 IRRADIANCE")]/parent::label',
        "RELATIVE HUMIDITY": '//*[@id="quick-analysis"]//span[contains(text(),"RELATIVE HUMIDITY")]/parent::label',
        "AIR PRESSURE": '//*[@id="quick-analysis"]//span[contains(text(),"AIR PRESSURE")]/parent::label',
        "AMBIENT TEMPERATURE": '//*[@id="quick-analysis"]//span[contains(text(),"AMBIENT TEMPERATURE")]/parent::label',
        "WIND DIRECTION ACTUAL": '//*[@id="quick-analysis"]//span[contains(text(),"WIND DIRECTION ACTUAL")]/parent::label',
        "PYRANOMETER 1 TEMPERATURE": '//*[@id="quick-analysis"]//span[contains(text(),"PYRANOMETER 1 TEMPERATURE")]/parent::label',
        "PYRANOMETER 2 TEMPERATURE": '//*[@id="quick-analysis"]//span[contains(text(),"PYRANOMETER 2 TEMPERATURE")]/parent::label',
        "PYRANOMETER 3 TEMPERATURE": '//*[@id="quick-analysis"]//span[contains(text(),"PYRANOMETER 3 TEMPERATURE")]/parent::label',

    }

class Elements:
    Elements = {
        'Universidad de Panama 1.1': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 1.1")]/parent::label',
        'UP1 INV1.1-01':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-01")]/parent::label',
        'UP1 INV1.1-02':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-02")]/parent::label',
        'UP1 INV1.1-03':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-03")]/parent::label',
        'UP1 INV1.1-04':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-04")]/parent::label',
        'UP1 INV1.1-05':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-05")]/parent::label',
        'UP1 INV1.1-06':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-06")]/parent::label',
        'UP1 INV1.1-07':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-07")]/parent::label',
        'UP1 INV1.1-08':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-08")]/parent::label',
        'UP1 INV1.1-09':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-09")]/parent::label',
        'UP1 INV1.1-10':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-10")]/parent::label',
        'UP1 INV1.1-11':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-11")]/parent::label',
        'UP1 INV1.1-12':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-12")]/parent::label',
        'UP1 INV1.1-13':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-13")]/parent::label',
        'UP1 INV1.1-14':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-14")]/parent::label',
        'UP1 INV1.1-15':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-15")]/parent::label',
        'UP1 INV1.1-16':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-16")]/parent::label',
        'UP1 INV1.1-17':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-17")]/parent::label',
        'UP1 INV1.1-18':'//*[@id="quick-analysis"]//span[contains(text(),"UP1 INV1.1-18")]/parent::label',
        'Universidad de Panama 1.2': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 1.2")]/parent::label',
        'UP2 INV1.2-01':'//*[@id="quick-analysis"]//span[contains(text(),"UP2 INV1.2-01")]/parent::label',
        'Universidad de Panama 2.1': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 2.1")]/parent::label',
        'Universidad de Panama 2.2': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 2.2")]/parent::label',
        'Universidad de Panama 3.1': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 3.1")]/parent::label',
        'Universidad de Panama 3.2': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 3.2")]/parent::label',
        'Universidad de Panama 4.1': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 4.1")]/parent::label',
        'Universidad de Panama 4.2': '//*[@id="quick-analysis"]//span[contains(text(),"Universidad Panamá 4.2")]/parent::label',
    }

class Typology:
    Typology = {
        "Inversor - (INVERSOR)": {
            "Elements": Elements.Elements, # Elementos a seleccionar
            "Parameters": Parameters.Parameters_inv,  # Parámetros generales
        },
        "Estación Meteorológica - (METEO)":{
            "Elements": Elements.Elements, # Elementos a seleccionar
            "Parameters": Parameters.Parameters_meteo,  # Parámetros generales

        }

    }
