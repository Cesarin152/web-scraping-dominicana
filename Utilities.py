import logging
import os
import re
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class DatePickerUtil:
    """
    Utilidad para seleccionar fechas en un datepicker genérico.
    Se asume que el datepicker se abre haciendo click en un input,
    y que posteriormente se interactúa con sus controles (mes, año, días).
    """
    @staticmethod
    def select_date(driver, day: int, month: str, year: int, wait_time: int = 10,
                    input_datapicker_xpath:str = '//input[@class="form-control form-control-sm"]',
                    datepicker_container_class_name: str = 'datepicker-dropdown',
                    datepicker_switch_xpath: str = '//th[@class="datepicker-switch"]',
                    prev_button_xpath: str = '//th[@class="prev"]'
                    ):
        """
        Selecciona la fecha dada (day-month-year) en un datepicker.
        Parámetros:
        -----------
        driver : WebDriver
            Instancia de Selenium WebDriver.
        day : int
            Día a seleccionar (1-31).
        month : str
            Nombre del mes en minúsculas o tal como se muestre en el datepicker. p.ej. "febrero"
        year : int
            Año a seleccionar. p.ej. 2025
        wait_time : int
            Tiempo máximo de espera para encontrar elementos del datepicker.
        datepicker_container_xpath : str
            XPATH que identifica el contenedor del datepicker. Ajustar según tu HTML.
        datepicker_switch_xpath : str
            XPATH que localiza el elemento “switch” (en muchos datepickers, es el que muestra “March 2025”).
        prev_button_xpath : str
            XPATH del botón de retroceso de mes o año.

        Importante:
        Esta lógica asume un datepicker de estilo “bootstrap datepicker”, donde
        cambiar de mes puede requerir pulsar flechas (prev/next). Ajustar según tu caso.
        """
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"Seleccionando fecha: {day}-{month}-{year}")
            wait = WebDriverWait(driver, wait_time)
            wait.until(EC.visibility_of_element_located((By.XPATH, input_datapicker_xpath))).click()
            # Esperar a que el contenedor del datepicker sea visible
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, datepicker_container_class_name)))

            # Asegurarnos de que podamos interactuar con el switch (que muestra mes y año)
            datepicker_switch = wait.until(EC.visibility_of_element_located((By.XPATH, datepicker_switch_xpath)))
            current_text = datepicker_switch.text.lower()  # Ejemplo: "March 2025"

            # Si necesitamos cambiar de año, abrimos vista de años (esto depende del datepicker).
            # A veces hay un segundo click en el switch para ver años, etc. Se ajusta según tu caso.
            # Este es un ejemplo muy simplificado que intenta chequear si el año difiere:
            current_year_match = re.search(r'(\d{4})', current_text)
            if current_year_match:
                current_year = int(current_year_match.group(1))
            else:
                # Si no hay match, se podría necesitar otro enfoque
                current_year = year

            # Moverse hacia atrás o adelante hasta encontrar el año deseado
            # (En algunos datepickers, se requiere pulsar "switch" y luego un "prev/next").
            # Aquí solo mostramos un ejemplo simplificado que navega mes a mes hacia atrás.
            while current_year != year:
                # Si el año actual es mayor que el deseado, pulsamos prev, de lo contrario next
                # (No tenemos un next_button_xpath, se podría agregar también.)
                if current_year > year:
                    prev_button = driver.find_element(By.XPATH, prev_button_xpath)
                    prev_button.click()
                else:
                    # Aquí agregamos un "next_button_xpath" según sea necesario
                    # next_button = driver.find_element(By.XPATH, next_button_xpath)
                    # next_button.click()
                    # Ejemplo: forzamos un break si no hay next button
                    raise NotImplementedError("Falta implementar el botón 'next' para avanzar años.")
                time.sleep(0.5)
                datepicker_switch = wait.until(EC.visibility_of_element_located((By.XPATH, datepicker_switch_xpath)))
                current_text = datepicker_switch.text.lower()
                # Actualizar current_year
                match = re.search(r'(\d{4})', current_text)
                if match:
                    current_year = int(match.group(1))

            # Una vez en el año correcto, movernos hasta el mes
            # Ejemplo muy simplificado: si “month” no está en "current_text", pulsamos prev:
            while month.lower() not in current_text:
                prev_button = driver.find_element(By.XPATH, prev_button_xpath)
                prev_button.click()
                time.sleep(0.5)
                datepicker_switch = wait.until(EC.visibility_of_element_located((By.XPATH, datepicker_switch_xpath)))
                current_text = datepicker_switch.text.lower()

            # Finalmente, seleccionamos el día
            day_xpath = f'//td[@class="day" and text()="{day}"]'
            day_element = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))
            day_element.click()

        except Exception as e:
            logger.error("Error al seleccionar la fecha en el datepicker.", exc_info=True)
            raise


class FileManagerUtil:
    """
    Utilidad para operaciones de manejo de archivos: renombrar, mover, etc.
    """

    @staticmethod
    def rename_file(old_name: str, new_name: str, directory: str = None):
        """
        Renombra un archivo en 'directory' (o en la carpeta de Descargas del usuario, si directory es None).
        Parámetros:
        -----------
        old_name : str
            Nombre o ruta actual del archivo.
        new_name : str
            Nuevo nombre (sin ruta) o ruta completa al que se desea renombrar el archivo.
        directory : str | None
            Directorio donde se encuentra el archivo y donde se renombrará. Si es None,
            se usa la carpeta de Descargas del usuario.
        """
        logger = logging.getLogger(__name__)
        try:
            if directory is None:
                directory = os.path.join(os.path.expanduser('~'), 'Downloads')

            old_file_path = os.path.join(directory, old_name)
            # Si new_name es solo el nombre, se renombra en el mismo directorio
            # Si quisieras permitir new_name con ruta absoluta, podrías validarlo.
            new_file_path = (new_name if os.path.isabs(new_name)
                             else os.path.join(directory, new_name))

            logger.info(f"Renombrando archivo: {old_file_path} -> {new_file_path}")
            os.rename(old_file_path, new_file_path)
        except FileNotFoundError:
            logger.error(f"Error: Archivo '{old_file_path}' no encontrado.", exc_info=True)
            raise
        except FileExistsError:
            logger.error(f"Error: El archivo '{new_file_path}' ya existe.", exc_info=True)
            raise
        except Exception as e:
            logger.error("Error inesperado al renombrar archivo.", exc_info=True)
            raise
