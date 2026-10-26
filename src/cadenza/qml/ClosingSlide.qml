import QtQuick

Rectangle {
    id: closing
    property real scaleUnit: 1
    color: "#101f19"
    Item {
        width: 1280 * closing.scaleUnit
        height: 720 * closing.scaleUnit
        anchors.horizontalCenter: parent.horizontalCenter
        Text {
            x: 60 * closing.scaleUnit; y: 45 * closing.scaleUnit
            text: "CADENZA × MANCHESTER CAMERATA"
            color: "#b4ef50"; font.pixelSize: 22 * closing.scaleUnit
            font.letterSpacing: 1.5 * closing.scaleUnit
        }
        Text {
            x: 60 * closing.scaleUnit; y: 95 * closing.scaleUnit
            text: "Thank you for taking part"
            color: "#f4f6e9"; font.pixelSize: 56 * closing.scaleUnit; font.bold: true
        }
        Text {
            objectName: "closingMessage"
            x: 60 * closing.scaleUnit; y: 200 * closing.scaleUnit
            width: 760 * closing.scaleUnit
            text: "Discover more about the Cadenza project\nand give us your feedback on today."
            color: "#f4f6e9"; font.pixelSize: 34 * closing.scaleUnit
            lineHeight: 1.35
        }
        Text {
            x: 60 * closing.scaleUnit; y: 322 * closing.scaleUnit
            text: "Scan the QR code or visit"
            color: "#f49bce"; font.pixelSize: 32 * closing.scaleUnit
        }
        Text {
            objectName: "closingUrl"
            x: 60 * closing.scaleUnit; y: 375 * closing.scaleUnit
            text: "cadenzachallenge.org/camerata/survey"
            color: "#b4ef50"; font.pixelSize: 33 * closing.scaleUnit
        }
        Rectangle {
            x: 60 * closing.scaleUnit; y: 446 * closing.scaleUnit
            width: 730 * closing.scaleUnit; height: 100 * closing.scaleUnit
            color: "white"; radius: 5 * closing.scaleUnit
            Image {
                objectName: "closingCadenzaLogo"
                x: 18 * closing.scaleUnit; y: 8 * closing.scaleUnit
                width: 180 * closing.scaleUnit; height: 84 * closing.scaleUnit
                source: "assets/logos/cadenza.png"; fillMode: Image.PreserveAspectFit
            }
            Image {
                objectName: "closingEpsrcLogo"
                x: 238 * closing.scaleUnit; y: 18 * closing.scaleUnit
                width: 470 * closing.scaleUnit; height: 64 * closing.scaleUnit
                source: "assets/logos/epsrc.png"; fillMode: Image.PreserveAspectFit
            }
        }
        Image {
            objectName: "closingQr"
            x: 860 * closing.scaleUnit; y: 206 * closing.scaleUnit
            width: 340 * closing.scaleUnit; height: 340 * closing.scaleUnit
            source: "assets/cadenza-qr.png"
            fillMode: Image.PreserveAspectFit
            smooth: false
        }
    }
}
