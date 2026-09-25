import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: operator
    visible: true; width: 1000; height: 850; minimumWidth: 800; minimumHeight: 810
    title: "Cadenza · Operator"; color: "#eef0f1"
    // A complete light control palette, independent of the macOS appearance.
    palette.window: "#eef0f1"
    palette.windowText: "#17232d"
    palette.text: "#17232d"
    palette.base: "#ffffff"
    palette.alternateBase: "#e4e8eb"
    palette.button: "#e2e7eb"
    palette.buttonText: "#17232d"
    palette.highlight: "#205b91"
    palette.highlightedText: "#ffffff"
    palette.toolTipBase: "#ffffff"
    palette.toolTipText: "#17232d"
    palette.light: "#ffffff"
    palette.midlight: "#e4e8eb"
    palette.mid: "#9aa6af"
    palette.dark: "#63717c"
    palette.shadow: "#384650"
    palette.disabled.windowText: "#64717b"
    palette.disabled.text: "#64717b"
    palette.disabled.buttonText: "#64717b"
    palette.disabled.button: "#e4e8eb"
    property var s: controller.state
    onClosing: Qt.quit()
    Shortcut { sequence: "Right"; onActivated: controller.move(1) }
    Shortcut { sequence: "Left"; onActivated: controller.move(-1) }
    Shortcut { sequence: "Space"; onActivated: controller.move(1) }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 24; spacing: 12
        RowLayout {
            Label { text: "CADENZA"; font.pixelSize: 26; font.bold: true; Layout.fillWidth: true }
            Label { text: "Slide " + (operator.s.index+1) + " / " + operator.s.count; font.pixelSize: 18 }
        }
        Slide { Layout.fillWidth: true; Layout.preferredHeight: width * 9/16; Layout.maximumHeight: 430 }
        Label { text: "UP NEXT   " + operator.s.nextTitle; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
        Label { text: operator.s.notes; wrapMode: Text.Wrap; Layout.fillWidth: true }
        RowLayout {
            Button { text: "← Back"; enabled: operator.s.index > 0; onClicked: controller.move(-1) }
            Button { text: "Next →"; enabled: operator.s.index < operator.s.count-1; highlighted: true; onClicked: controller.move(1) }
            Item { Layout.fillWidth: true }
            Label { text: "Captions" }
            ComboBox { model: ["AUTO", "ON", "OFF"]; onActivated: controller.setOverride(currentText) }
            Label { text: operator.s.captions ? "Visible" : "Hidden" }
        }
        RowLayout {
            visible: operator.s.hasTimer
            Label { text: "Timer  " + operator.s.timerTime; font.family: "Menlo"; font.bold: true }
            Button { text: operator.s.timerAction; enabled: operator.s.timerActionEnabled; onClicked: controller.timerToggle() }
            Button { text: operator.s.timerSecondary; enabled: operator.s.timerSecondaryEnabled; onClicked: controller.timerStopRestart() }
            Item { Layout.fillWidth: true }
        }
        RowLayout {
            Label { text: "Audience display" }
            ComboBox {
                id: screens; Layout.fillWidth: true; model: Qt.application.screens
                textRole: "name"
            }
            Button { text: "Present full screen"; onClicked: { audience.screen = Qt.application.screens[screens.currentIndex]; audience.showFullScreen(); } }
            Button { text: "Windowed"; onClicked: { audience.showNormal(); audience.raise(); operator.raise(); } }
        }
        Label { text: operator.s.status; wrapMode: Text.Wrap; Layout.fillWidth: true; color: "#40576a" }
    }
    Window {
        id: audience
        title: "Cadenza · Audience"; visible: true; width: 1280; height: 720
        color: "#101922"
        onClosing: audience.hide()
        Slide { anchors.fill: parent }
        Shortcut { sequence: "Escape"; onActivated: { audience.showNormal(); operator.raise(); } }
        Shortcut { sequence: "Right"; onActivated: controller.move(1) }
        Shortcut { sequence: "Left"; onActivated: controller.move(-1) }
        Shortcut { sequence: "Space"; onActivated: controller.move(1) }
    }
}
