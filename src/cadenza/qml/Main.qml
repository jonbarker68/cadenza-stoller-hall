import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: operator
    visible: true; width: 1000; height: 900; minimumWidth: 800; minimumHeight: 860
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
    Shortcut { enabled: !slidePicker.popup.visible; sequence: "Right"; onActivated: controller.move(1) }
    Shortcut { enabled: !slidePicker.popup.visible; sequence: "Left"; onActivated: controller.move(-1) }
    Shortcut { enabled: !slidePicker.popup.visible; sequence: "Space"; onActivated: controller.move(1) }
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 24; spacing: 12
        RowLayout {
            Layout.minimumHeight: 36; Layout.maximumHeight: 36
            Label { text: "CADENZA"; font.pixelSize: 26; font.bold: true; Layout.fillWidth: true }
            Label { text: "Slide " + (operator.s.index+1) + " / " + operator.s.count; font.pixelSize: 18 }
        }
        RowLayout {
            Layout.minimumHeight: 36; Layout.maximumHeight: 36
            Label { text: "Jump to slide" }
            ComboBox {
                id: slidePicker
                objectName: "slidePicker"
                Layout.fillWidth: true
                model: controller.slideChoices
                currentIndex: operator.s.index
                Accessible.name: "Jump to slide"
                onActivated: function(index) { controller.jumpToSlide(index) }
            }
        }
        RowLayout {
            Layout.minimumHeight: 36; Layout.maximumHeight: 36
            Button { objectName: "backButton"; Layout.preferredWidth: 110; text: "← Back"; enabled: operator.s.index > 0; onClicked: controller.move(-1) }
            Button { objectName: "nextButton"; Layout.preferredWidth: 110; text: "Next →"; enabled: operator.s.index < operator.s.count-1; highlighted: true; onClicked: controller.move(1) }
            Item { Layout.fillWidth: true }
            Label { text: "Captions" }
            ComboBox { model: ["AUTO", "ON", "OFF"]; onActivated: controller.setOverride(currentText) }
            Label { text: operator.s.captions ? "Visible" : "Hidden" }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 120
            Slide {
                anchors.centerIn: parent
                width: Math.min(parent.width, parent.height * 16 / 9)
                height: width * 9 / 16
            }
        }
        Label {
            text: "UP NEXT   " + operator.s.nextTitle
            font.bold: true
            Layout.fillWidth: true
            Layout.minimumHeight: 24; Layout.maximumHeight: 24
            elide: Text.ElideRight
            ToolTip.visible: hovered
            ToolTip.text: text
            property bool hovered: nextHover.hovered
            HoverHandler { id: nextHover }
        }
        ScrollView {
            id: notesView
            objectName: "operatorNotes"
            Layout.fillWidth: true
            Layout.minimumHeight: 80; Layout.maximumHeight: 80
            clip: true
            contentWidth: width - 24
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn
            Label {
                width: notesView.width - 24
                text: operator.s.notes
                wrapMode: Text.Wrap
            }
            Connections {
                target: controller
                function onChanged() {
                    if (notesView.lastSlide !== operator.s.index) {
                        notesView.contentItem.contentY = 0
                        notesView.lastSlide = operator.s.index
                    }
                }
            }
            property int lastSlide: -1
        }
        RowLayout {
            Label { text: "Speaker colours" }
            ComboBox {
                objectName: "speakerModeControl"
                model: ["AUTO", "WHITE", "SPEAKERS"]
                enabled: operator.s.speakerAvailable
                currentIndex: model.indexOf(operator.s.speakerOverride)
                onActivated: controller.setSpeakerOverride(currentText)
            }
            Label {
                Layout.fillWidth: true
                text: !operator.s.speakerAvailable ? "Unavailable — start with speaker estimation and BBC Live layout"
                    : operator.s.captionSpeakerColours ? "Speaker colours active" : "White captions"
                wrapMode: Text.Wrap
            }
        }
        RowLayout {
            Layout.minimumHeight: 36; Layout.maximumHeight: 36
            opacity: operator.s.hasTimer ? 1 : 0
            enabled: operator.s.hasTimer
            Label { text: "Timer  " + operator.s.timerTime; font.family: "Menlo"; font.bold: true }
            Button { text: operator.s.timerAction; enabled: operator.s.timerActionEnabled; onClicked: controller.timerToggle() }
            Button { text: operator.s.timerSecondary; enabled: operator.s.timerSecondaryEnabled; onClicked: controller.timerStopRestart() }
            Item { Layout.fillWidth: true }
        }
        RowLayout {
            visible: operator.s.layout === "closing-credits"
            Label { text: "Credits" }
            Button { text: operator.s.creditsPaused ? "Resume credits" : "Pause credits"; onClicked: controller.toggleCredits() }
            Button { text: "Restart credits"; onClicked: controller.restartCredits() }
        }
        RowLayout {
            Label { text: "Audience display" }
            ComboBox {
                id: screens; objectName: "audienceScreenSelector"; Layout.fillWidth: true; model: Qt.application.screens
                textRole: "name"
                onActivated: controller.presentAudience(audience, currentIndex, audience.visibility === Window.FullScreen)
            }
            Button { objectName: "presentFullScreenButton"; text: "Present full screen"; onClicked: { controller.presentAudience(audience, screens.currentIndex, true); } }
            Button { objectName: "audienceWindowedButton"; text: "Windowed"; onClicked: { controller.presentAudience(audience, screens.currentIndex, false); operator.raise(); } }
        }
        Label { text: operator.s.status; wrapMode: Text.Wrap; Layout.fillWidth: true; color: operator.s.error ? "#a12424" : "#40576a" }
        Label { text: "Log: " + operator.s.logPath; visible: operator.s.logPath.length > 0; font.pixelSize: 12; Layout.fillWidth: true; elide: Text.ElideMiddle }
    }
    Window {
        id: audience
        title: "Cadenza · Audience"; visible: true; width: 1280; height: 720
        color: DisplayStyle.background
        onClosing: { controller.cancelAudiencePresentation(); audience.hide(); }
        Slide { anchors.fill: parent }
        Shortcut { sequence: "Escape"; onActivated: { controller.cancelAudiencePresentation(); audience.showNormal(); operator.raise(); } }
        Shortcut { sequence: "Right"; onActivated: controller.move(1) }
        Shortcut { sequence: "Left"; onActivated: controller.move(-1) }
        Shortcut { sequence: "Space"; onActivated: controller.move(1) }
    }
}
