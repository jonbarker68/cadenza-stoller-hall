import QtQuick

Rectangle {
    id: welcome
    property var state
    property real unit: Math.min(width / 1280, height / 720)
    color: "#101f19"
    clip: true

    Image {
        objectName: "arrivalsPhoto"
        x: parent.width * 0.43
        width: parent.width - x
        height: parent.height
        source: "assets/orchestra.jpg"
        fillMode: Image.PreserveAspectCrop
        horizontalAlignment: Image.AlignHCenter
        verticalAlignment: Image.AlignBottom
    }
    Rectangle {
        width: parent.width * 0.47
        height: parent.height
        color: "#101f19"
    }
    Rectangle {
        x: parent.width * 0.47
        width: 5 * welcome.unit
        height: parent.height
        color: "#b4ef50"
    }
    Column {
        x: 52 * welcome.unit
        y: 48 * welcome.unit
        width: parent.width * 0.47 - 90 * welcome.unit
        spacing: 22 * welcome.unit
        Text {
            text: "CADENZA PROJECT\n× MANCHESTER CAMERATA"
            color: "#b4ef50"
            font.pixelSize: 19 * welcome.unit
            font.letterSpacing: 1.5 * welcome.unit
            lineHeight: 1.3
        }
        Rectangle {
            width: 90 * welcome.unit
            height: 5 * welcome.unit
            color: "#f49bce"
        }
        Text {
            width: parent.width
            text: welcome.state.title
            textFormat: Text.PlainText
            color: "#f4f6e9"
            font.pixelSize: 66 * welcome.unit
            font.weight: Font.Bold
            wrapMode: Text.Wrap
            lineHeight: 0.95
        }
        Text {
            width: parent.width
            text: welcome.state.body
            textFormat: Text.PlainText
            color: "#e1e9dc"
            font.pixelSize: 26 * welcome.unit
            lineHeight: 1.2
            wrapMode: Text.Wrap
        }
        Text {
            text: "STOLLER HALL\n29 OCTOBER 2026 · 3 PM"
            color: "#b4ef50"
            font.pixelSize: 20 * welcome.unit
            lineHeight: 1.4
        }
    }
    Column {
        x: 52 * welcome.unit
        y: parent.height - 125 * welcome.unit
        spacing: 10 * welcome.unit
        Text {
            text: "Welcome. Please take your seats."
            color: "#f49bce"
            font.pixelSize: 25 * welcome.unit
            font.weight: Font.DemiBold
        }
        Text {
            text: "The concert will begin shortly."
            color: "#e1e9dc"
            font.pixelSize: 22 * welcome.unit
        }
    }
}
