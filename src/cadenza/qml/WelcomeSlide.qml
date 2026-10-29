import QtQuick

Item {
    id: welcome
    property var state
    property real scaleUnit: 1
    // Keep the whole layout on the same reference canvas as the captions.
    Item {
        width: DisplayStyle.referenceWidth * welcome.scaleUnit
        height: DisplayStyle.referenceHeight * welcome.scaleUnit
        anchors.horizontalCenter: parent.horizontalCenter

        Text {
            objectName: "welcomeTitle"
            x: 70 * welcome.scaleUnit
            y: 90 * welcome.scaleUnit
            width: 1140 * welcome.scaleUnit
            text: welcome.state.title
            textFormat: Text.PlainText
            font.pixelSize: 42 * welcome.scaleUnit
            font.weight: Font.DemiBold
            color: DisplayStyle.titleText
            wrapMode: Text.Wrap
        }
        Text {
            objectName: "welcomeIntroduction"
            x: 70 * welcome.scaleUnit
            y: 192 * welcome.scaleUnit
            width: 1140 * welcome.scaleUnit
            text: welcome.state.body
            textFormat: Text.PlainText
            font.pixelSize: 32 * welcome.scaleUnit
            color: DisplayStyle.bodyText
            wrapMode: Text.Wrap
        }

        Rectangle {
            objectName: "welcomeLogoPanel"
            x: 70 * welcome.scaleUnit
            y: 270 * welcome.scaleUnit
            width: 1140 * welcome.scaleUnit
            height: 270 * welcome.scaleUnit
            color: "white"
            radius: 5 * welcome.scaleUnit

            Text {
                x: 28 * welcome.scaleUnit
                y: 15 * welcome.scaleUnit
                text: "CADENZA & MANCHESTER CAMERATA"
                color: "#263542"
                font.pixelSize: 15 * welcome.scaleUnit
                font.letterSpacing: welcome.scaleUnit
            }
            Image {
                objectName: "logoCadenza"
                x: 35 * welcome.scaleUnit
                y: 42 * welcome.scaleUnit
                width: 155 * welcome.scaleUnit
                height: 95 * welcome.scaleUnit
                source: "assets/logos/cadenza.png"
                fillMode: Image.PreserveAspectFit
            }
            Image {
                objectName: "logoCamerata"
                x: 252 * welcome.scaleUnit
                y: 43 * welcome.scaleUnit
                width: 92 * welcome.scaleUnit
                height: 92 * welcome.scaleUnit
                source: "assets/logos/camerata.png"
                fillMode: Image.PreserveAspectFit
            }
            Text {
                x: 680 * welcome.scaleUnit
                y: 15 * welcome.scaleUnit
                text: "FUNDED BY"
                color: "#263542"
                font.pixelSize: 15 * welcome.scaleUnit
                font.letterSpacing: welcome.scaleUnit
            }
            Image {
                objectName: "logoEpsrc"
                x: 680 * welcome.scaleUnit
                y: 44 * welcome.scaleUnit
                width: 415 * welcome.scaleUnit
                height: 95 * welcome.scaleUnit
                source: "assets/logos/epsrc.png"
                fillMode: Image.PreserveAspectFit
            }
            Rectangle {
                x: 28 * welcome.scaleUnit
                y: 150 * welcome.scaleUnit
                width: parent.width - 56 * welcome.scaleUnit
                height: welcome.scaleUnit
                color: "#dce1e4"
            }
            Text {
                x: 28 * welcome.scaleUnit
                y: 162 * welcome.scaleUnit
                text: "UNIVERSITY ORGANISERS"
                color: "#263542"
                font.pixelSize: 15 * welcome.scaleUnit
                font.letterSpacing: welcome.scaleUnit
            }
            Row {
                x: 28 * welcome.scaleUnit
                y: 181 * welcome.scaleUnit
                spacing: 25 * welcome.scaleUnit
                Repeater {
                    model: ["salford.png", "leeds.svg", "nottingham.svg", "sheffield.svg"]
                    Image {
                        objectName: "logoUniversity" + index
                        width: 252 * welcome.scaleUnit
                        // Sheffield's compact mark needs a taller display
                        // box to balance the other university wordmarks.
                        y: modelData === "sheffield.svg" ? 0 : 7 * welcome.scaleUnit
                        height: (modelData === "sheffield.svg" ? 84 : 70) * welcome.scaleUnit
                        source: "assets/logos/" + modelData
                        sourceSize.width: 504
                        sourceSize.height: modelData === "sheffield.svg" ? 168 : 140
                        fillMode: Image.PreserveAspectFit
                    }
                }
            }
        }
    }
}
