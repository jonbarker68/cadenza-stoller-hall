import QtQuick

Rectangle {
    id: slide
    color: "#101922"
    property var state: controller.state
    property real scaleUnit: Math.min(width / 1280, height / 720)
    Rectangle { x: 0; y: 0; width: parent.width; height: 5 * slide.scaleUnit; color: "#d9b679" }
    Text { x: 70 * slide.scaleUnit; y: 48 * slide.scaleUnit; text: "CADENZA  /  STOLLER HALL"; color: "#d9b679"; font.pixelSize: 18 * slide.scaleUnit; font.letterSpacing: 3 * slide.scaleUnit }
    Column {
        x: 70 * slide.scaleUnit; y: 145 * slide.scaleUnit; width: parent.width - 140 * slide.scaleUnit
        spacing: 24 * slide.scaleUnit
        Text { width: parent.width; text: slide.state.title; color: "#f5f1e8"; font.pixelSize: 56 * slide.scaleUnit; font.weight: Font.DemiBold; wrapMode: Text.Wrap }
        Text { width: parent.width; text: slide.state.body; color: "#becad1"; font.pixelSize: 29 * slide.scaleUnit; wrapMode: Text.Wrap }
        Text { visible: slide.state.kind === "experiment"; text: "PASSAGE " + slide.state.passage + "     ·     PAGE " + slide.state.page; color: "#d9b679"; font.pixelSize: 32 * slide.scaleUnit }
    }
    Text {
        objectName: "musicCountup"
        visible: slide.state.kind === "countup"
        anchors.horizontalCenter: parent.horizontalCenter
        y: 315 * slide.scaleUnit
        width: parent.width - 140 * slide.scaleUnit
        height: 215 * slide.scaleUnit
        text: slide.state.timerTime
        color: "#f5f1e8"
        font.family: "Menlo"
        font.pixelSize: 180 * slide.scaleUnit
        font.weight: Font.DemiBold
        fontSizeMode: Text.Fit
        minimumPixelSize: 12
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    Item {
        visible: slide.state.kind === "response"
        width: 205 * slide.scaleUnit; height: width
        anchors.horizontalCenter: parent.horizontalCenter; y: 335 * slide.scaleUnit
        Canvas {
            id: ring; anchors.fill: parent
            property real fraction: slide.state.fraction
            onFractionChanged: requestPaint()
            onWidthChanged: requestPaint()
            onPaint: {
                var ctx = getContext("2d"); ctx.reset();
                var r = width / 2 - 9 * slide.scaleUnit;
                ctx.lineWidth = 9 * slide.scaleUnit; ctx.strokeStyle = "#2b3945";
                ctx.beginPath(); ctx.arc(width/2,height/2,r,0,2*Math.PI); ctx.stroke();
                ctx.strokeStyle = "#d9b679"; ctx.beginPath(); ctx.arc(width/2,height/2,r,-Math.PI/2,-Math.PI/2+2*Math.PI*fraction); ctx.stroke();
            }
        }
        Text { anchors.centerIn: parent; text: slide.state.timerTime; color: "#f5f1e8"; font.pixelSize: 42 * slide.scaleUnit; font.family: "Menlo" }
    }
    Rectangle {
        visible: slide.state.captions && slide.state.caption.length > 0
        anchors.bottom: parent.bottom; anchors.bottomMargin: 32 * slide.scaleUnit
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 100 * slide.scaleUnit; height: captionText.implicitHeight + 24 * slide.scaleUnit
        color: "#050a0e"; radius: 8 * slide.scaleUnit
        Text { id: captionText; anchors.centerIn: parent; width: parent.width-36*slide.scaleUnit; text: slide.state.caption; color: "white"; font.pixelSize: 31 * slide.scaleUnit; wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter }
    }
}
