import QtQuick

Rectangle {
    id: closing
    objectName: "creditsScreen"
    property real pdfOffset: 0
    property real pdfPageHeight: 650
    function pdfMetrics() {
        var atoms = [], groups = []
        function textLines(item, origin) {
            if (!item.text.length || !item.lineCount) return
            var step = item.contentHeight / item.lineCount
            for (var n = 0; n < item.lineCount; n++)
                atoms.push([origin + item.y / scaleUnit + n * step / scaleUnit,
                            origin + item.y / scaleUnit + (n + 1) * step / scaleUnit])
        }
        textLines(creditsHeading, 0)
        for (var i = 0; i < sections.count; i++) {
            var group = sections.itemAt(i), origin = group.y / scaleUnit
            groups.push([origin, origin + group.height / scaleUnit])
            textLines(group.headingItem, origin)
            var names = group.namesItem
            for (var n = 0; n < names.entries.count; n++) {
                var person = names.entries.itemAt(n)
                var personOrigin = origin + (names.y + person.y) / scaleUnit
                textLines(person.nameItem, personOrigin)
                textLines(person.roleItem, personOrigin)
            }
            var logo = group.logoItem
            if (logo.visible) atoms.push([origin + logo.y / scaleUnit,
                                         origin + (logo.y + logo.height) / scaleUnit])
        }
        return JSON.stringify({atoms: atoms, groups: groups})
    }
    property real scaleUnit: 1
    property var state: controller.state
    readonly property bool whiteCredits: state.credits.theme === "white"
    readonly property color creditsBackground: whiteCredits ? "#ffffff" : "#101f19"
    readonly property color creditsHeadingColor: whiteCredits ? "#174b36" : "#b4ef50"
    readonly property color creditsNameColor: whiteCredits ? "#253c32" : "#f4f6e9"
    readonly property color creditsIntroColor: whiteCredits ? "#913567" : "#f49bce"
    color: "#101f19"
    Item {
        width: 1280 * closing.scaleUnit
        height: 720 * closing.scaleUnit
        anchors.horizontalCenter: parent.horizontalCenter
        Item {
            x: 40 * closing.scaleUnit
            width: 610 * closing.scaleUnit
            height: parent.height
            Text {
                y: 35 * closing.scaleUnit
                text: "CADENZA × MANCHESTER CAMERATA"
                color: "#b4ef50"; font.pixelSize: 21 * closing.scaleUnit
            }
            Text {
                y: 88 * closing.scaleUnit
                text: "Thank you for\ntaking part"
                color: "#f4f6e9"; font.pixelSize: 56 * closing.scaleUnit; font.bold: true
            }
            Text {
                y: 238 * closing.scaleUnit
                text: "Discover more and share your feedback"
                color: "#f49bce"; font.pixelSize: 28 * closing.scaleUnit
            }
            Image {
                objectName: "closingQr"
                x: 100 * closing.scaleUnit; y: 294 * closing.scaleUnit
                width: 320 * closing.scaleUnit; height: width
                source: "assets/cadenza-qr.png"
                fillMode: Image.PreserveAspectFit; smooth: false
            }
            Text {
                y: 640 * closing.scaleUnit
                text: "cadenzachallenge.org/camerata/survey"
                color: "#b4ef50"; font.pixelSize: 29 * closing.scaleUnit
            }
        }
        Rectangle {
            x: 674 * closing.scaleUnit
            width: parent.width - x
            height: parent.height
            color: closing.creditsBackground
        }
        Rectangle {
            x: 672 * closing.scaleUnit; y: 35 * closing.scaleUnit
            width: 2 * closing.scaleUnit; height: 650 * closing.scaleUnit
            color: "#b4ef50"; opacity: 0.45
        }
        Item {
            id: viewport
            objectName: "creditsViewport"
            x: 705 * closing.scaleUnit
            width: 540 * closing.scaleUnit
            y: closing.state.staticExport ? 35 * closing.scaleUnit : 0
            height: closing.state.staticExport ? closing.pdfPageHeight * closing.scaleUnit : parent.height
            clip: true
            Column {
                id: reel
                objectName: "creditsReel"
                width: parent.width
                spacing: 64 * closing.scaleUnit
                property real travel: height / closing.scaleUnit + 720
                property real cycle: travel / closing.state.credits.speed + closing.state.credits.pause_seconds
                y: closing.state.staticExport ? -closing.pdfOffset * closing.scaleUnit
                   : (720 - Math.min(travel, (closing.state.creditsElapsed % cycle) * closing.state.credits.speed)) * closing.scaleUnit
                Text {
                    id: creditsHeading
                    width: parent.width
                    text: closing.state.credits.heading
                    textFormat: Text.PlainText
                    wrapMode: Text.Wrap
                    horizontalAlignment: Text.AlignHCenter
                    color: closing.creditsIntroColor; font.pixelSize: 30 * closing.scaleUnit
                }
                Repeater {
                    id: sections
                    model: closing.state.credits.sections
                    Column {
                        width: reel.width
                        spacing: 20 * closing.scaleUnit
                        property alias headingItem: groupHeading
                        property alias logoItem: groupLogo
                        property alias namesItem: groupNames
                        Text {
                            id: groupHeading
                            width: parent.width; text: modelData.heading
                            textFormat: Text.PlainText; wrapMode: Text.Wrap
                            horizontalAlignment: Text.AlignHCenter
                            color: closing.creditsHeadingColor; font.pixelSize: 30 * closing.scaleUnit
                        }
                        Rectangle {
                            id: groupLogo
                            visible: !!modelData.logo
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: (modelData.logo_width || 320) * closing.scaleUnit
                            height: (modelData.logo_height || 80) * closing.scaleUnit
                            color: "white"; radius: 3 * closing.scaleUnit
                            Image {
                                anchors.fill: parent; anchors.margins: 6 * closing.scaleUnit
                                source: modelData.logo || ""
                                fillMode: Image.PreserveAspectFit
                            }
                        }
                        Column {
                            id: groupNames
                            visible: people.count > 0
                            width: parent.width
                            property alias entries: people
                            Repeater {
                                id: people
                                model: modelData.entries
                                Column {
                                    width: groupNames.width
                                    spacing: 3 * closing.scaleUnit
                                    property alias nameItem: personName
                                    property alias roleItem: personRole
                                    Text {
                                        id: personName
                                        width: parent.width; text: modelData.name
                                        height: text.length ? implicitHeight : 14 * closing.scaleUnit
                                        textFormat: Text.PlainText; wrapMode: Text.Wrap
                                        horizontalAlignment: Text.AlignHCenter
                                        color: closing.creditsNameColor; font.pixelSize: 28 * closing.scaleUnit
                                    }
                                    Text {
                                        id: personRole
                                        objectName: "creditRole"
                                        visible: text.length > 0
                                        width: parent.width; text: modelData.role
                                        textFormat: Text.PlainText; wrapMode: Text.Wrap
                                        horizontalAlignment: Text.AlignHCenter
                                        color: closing.creditsNameColor
                                        font.pixelSize: 24 * closing.scaleUnit; font.italic: true
                                    }
                                    Item { width: 1; height: 12 * closing.scaleUnit; visible: personRole.visible }
                                }
                            }
                        }
                    }
                }
            }
            Rectangle {
                width: parent.width; height: 55 * closing.scaleUnit
                visible: !closing.state.staticExport
                gradient: Gradient {
                    GradientStop { position: 0; color: closing.creditsBackground }
                    GradientStop { position: 1; color: Qt.rgba(closing.creditsBackground.r, closing.creditsBackground.g, closing.creditsBackground.b, 0) }
                }
            }
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width; height: 55 * closing.scaleUnit
                visible: !closing.state.staticExport
                gradient: Gradient {
                    GradientStop { position: 0; color: Qt.rgba(closing.creditsBackground.r, closing.creditsBackground.g, closing.creditsBackground.b, 0) }
                    GradientStop { position: 1; color: closing.creditsBackground }
                }
            }
        }
    }
}
