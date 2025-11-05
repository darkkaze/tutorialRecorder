Feature: Gestión de Proyectos
  Como usuario de TutorialRecorder
  Quiero gestionar mis proyectos de grabación
  Para organizar mis videotutoriales

  Scenario: Crear nuevo proyecto
    Given el usuario abre la aplicación
    When selecciona "Nuevo Proyecto"
    Then se muestra la ventana de configuración de proyecto
    And la ventana es alargada verticalmente y angosta
    And contiene campo "Nombre del Proyecto"
    And contiene sección "Inputs de Audio"
    And contiene sección "Inputs de Video"
    And contiene botón "Grabar"

  Scenario: Editar proyecto existente
    Given el usuario tiene proyectos guardados
    When selecciona "Editar Proyecto"
    And elige un proyecto de la lista
    Then se carga la configuración guardada del proyecto
    And puede modificar los inputs configurados

  Scenario: Importar proyecto
    Given el usuario tiene un archivo de proyecto
    When selecciona "Importar Proyecto"
    And elige el archivo del proyecto
    Then se carga el proyecto con su configuración
    And se muestran los inputs previamente configurados

Feature: Configuración de Inputs de Audio
  Como usuario
  Quiero configurar mis fuentes de audio
  Para capturar múltiples micrófonos simultáneamente

  Scenario: Seleccionar micrófono principal
    Given estoy en la ventana de configuración de proyecto
    When veo la sección "Inputs de Audio"
    Then hay un select box con la lista de micrófonos disponibles
    And puedo seleccionar mi micrófono

  Scenario: Agregar múltiples micrófonos
    Given he seleccionado un micrófono
    When presiono el botón "+"
    Then aparece un nuevo select box para otro micrófono
    And puedo seleccionar un segundo micrófono
    And puedo repetir el proceso para más micrófonos

  Scenario: Remover input de audio
    Given tengo múltiples inputs de audio configurados
    When presiono el botón "-" junto a un input
    Then ese input se elimina de la configuración

Feature: Configuración de Inputs de Video
  Como usuario
  Quiero configurar mis fuentes de video
  Para grabar webcam y pantalla simultáneamente

  Scenario: Configurar inputs de video por defecto
    Given estoy en la ventana de configuración de proyecto
    When veo la sección "Inputs de Video"
    Then hay 2 select boxes para entradas de video
    And puedo seleccionar "Webcam" en el primero
    And puedo seleccionar "Screen Capture" en el segundo

  Scenario: Agregar más inputs de video
    Given he configurado 2 inputs de video
    When presiono el botón "+" en la sección de video
    Then aparece un nuevo select box para otra fuente de video
    And puedo seleccionar otra webcam o pantalla

Feature: Selección de Área de Pantalla
  Como usuario
  Quiero seleccionar el área de pantalla a grabar
  Para capturar solo la región relevante

  Scenario: Activar selector de área de pantalla
    Given he seleccionado "Screen Capture" como input de video
    Then aparece un recuadro de selección en la pantalla
    And aparece un menú alargado flotante con controles

  Scenario: Cambiar aspect ratio de captura
    Given el selector de área está activo
    When selecciono un aspect ratio del menú (16:9, 9:16, 4:3, 1:1)
    Then el recuadro de selección cambia sus proporciones
    And mantiene el área aproximada pero ajustada al nuevo ratio

  Scenario: Mover área de captura
    Given el recuadro de selección está visible
    When arrastro el recuadro a otra posición
    Then el recuadro se mueve a la nueva ubicación
    And el área de captura se actualiza

  Scenario: Redimensionar área de captura
    Given el recuadro de selección está visible
    When arrastro las esquinas o bordes del recuadro
    Then el recuadro cambia de tamaño
    And respeta el aspect ratio seleccionado

Feature: Grabación de Proyecto
  Como usuario
  Quiero iniciar la grabación de todos los inputs
  Para capturar mi videotutorial

  Scenario: Iniciar grabación
    Given he configurado todos mis inputs
    And he dado nombre al proyecto
    When presiono el botón "Grabar"
    Then se inicia la grabación de todos los inputs de audio
    And se inicia la grabación de todos los inputs de video
    And todos los streams están sincronizados por timestamp
    And la ventana de configuración se oculta o minimiza
    And aparece la toolbar de control transparente

  Scenario: Toolbar de control visible durante grabación
    Given la grabación está en curso
    Then la toolbar transparente está visible
    And muestra la resolución del área de captura
    And contiene botón "Pausar"
    And contiene botón "Detener"
    And la toolbar es alargada horizontalmente y corta verticalmente
    And puedo mover la toolbar por el escritorio

Feature: Control de Grabación
  Como usuario
  Quiero controlar la grabación en progreso
  Para pausar cuando sea necesario

  Scenario: Pausar grabación
    Given la grabación está activa
    When presiono el botón "Pausar" en la toolbar
    Then la grabación se pausa en todos los inputs
    And el botón cambia a "Reanudar"
    And el timestamp de pausa se registra

  Scenario: Reanudar grabación
    Given la grabación está en pausa
    When presiono el botón "Reanudar"
    Then la grabación continúa en todos los inputs
    And el botón cambia a "Pausar"
    And la sincronización se mantiene

  Scenario: Detener grabación
    Given la grabación está activa o en pausa
    When presiono el botón "Detener" en la toolbar
    Then la grabación finaliza en todos los inputs
    And los archivos se guardan en carpeta temporal
    And la carpeta temporal tiene el nombre del proyecto
    And cada input se guarda como archivo separado
    And la toolbar desaparece
    And la ventana de configuración reaparece
    And el botón "Grabar" cambia a "Exportar"

  Scenario: Ocultar/mostrar toolbar manualmente
    Given la toolbar está visible durante la grabación
    When el usuario oculta la toolbar manualmente
    Then la toolbar desaparece de la pantalla
    And aparece en la barra del sistema (system tray)
    
  Scenario: Restaurar toolbar desde system tray
    Given la toolbar está oculta en system tray
    When el usuario hace clic en el icono de la aplicación
    Then la toolbar reaparece en pantalla
    And mantiene su última posición

Feature: Exportación de Proyecto
  Como usuario
  Quiero exportar los archivos grabados
  Para trabajar con ellos en edición

  Scenario: Exportar proyecto después de grabar
    Given he detenido una grabación
    And el botón "Exportar" está visible
    When presiono el botón "Exportar"
    Then se abre un diálogo de selección de carpeta
    
  Scenario: Seleccionar destino de exportación
    Given el diálogo de exportación está abierto
    When selecciono una carpeta de destino
    And confirmo la exportación
    Then todos los archivos de audio se copian a la carpeta
    And todos los archivos de video se copian a la carpeta
    And se copia el archivo de metadatos del proyecto
    And se muestra confirmación de exportación exitosa

  Scenario: Estructura de archivos exportados
    Given he exportado un proyecto
    Then la carpeta contiene:
      | archivo                    | descripción                    |
      | project_name_screen.mp4   | grabación de pantalla          |
      | project_name_webcam.mp4   | grabación de webcam            |
      | project_name_mic1.wav     | audio de micrófono 1           |
      | project_name_mic2.wav     | audio de micrófono 2 (si hay)  |
      | project_name_metadata.json| timestamps y configuración     |
