import QtQuick

Rectangle {
    id: band
    property var state
    property real scaleUnit: 1
    property real textWidthRef: DisplayStyle.referenceWidth - 2 * DisplayStyle.captionSideMargin
                                - 2 * DisplayStyle.captionPaddingX
    property real lineHeight: state.captionLineHeight * scaleUnit
    property int seenSerial: -1
    property string targetText: ""
    property string outgoing: ""
    property string displayText: ""

    visible: state.captions && state.caption.length > 0
    width: (DisplayStyle.referenceWidth - 2 * DisplayStyle.captionSideMargin) * scaleUnit
    height: Math.max(DisplayStyle.captionBandHeight * scaleUnit,
                     2 * lineHeight + 2 * DisplayStyle.captionPaddingY * scaleUnit)
    color: DisplayStyle.captionBackground
    radius: DisplayStyle.captionRadius * scaleUnit

    Component.onCompleted: {
        controller.configureCaptionLayout(DisplayStyle.captionFontFamily,
                                          Math.round(DisplayStyle.captionFontPx), textWidthRef)
        updateCaption()
    }
    onStateChanged: updateCaption()

    function settle(text) {
        scroll.stop()
        targetText = text
        displayText = text
        captionText.y = 0
    }
    function updateCaption() {
        if (!state || seenSerial === state.captionSerial)
            return
        seenSerial = state.captionSerial
        var text = state.caption
        if (!text || !state.captions) {
            settle("")
            return
        }
        if (scroll.running) {
            if (!state.captionScroll && targetText.split("\n")[0] === text.split("\n")[0]) {
                targetText = text
                displayText = outgoing + "\n" + text
            } else {
                settle(text)
            }
            return
        }
        if (state.captionScroll === 1 && state.captionScrollMs > 0 && targetText.length > 0) {
            outgoing = targetText.split("\n")[0]
            targetText = text
            displayText = outgoing + "\n" + text
            scroll.start()
        } else {
            settle(text)
        }
    }

    Item {
        id: viewport
        anchors.centerIn: parent
        width: band.textWidthRef * band.scaleUnit
        height: 2 * band.lineHeight
        clip: true
        Text {
            id: captionText
            objectName: "captionText"
            width: viewport.width
            text: band.displayText
            textFormat: Text.PlainText
            color: DisplayStyle.captionText
            font.family: DisplayStyle.captionFontFamily
            font.pixelSize: Math.round(DisplayStyle.captionFontPx) * band.scaleUnit
            wrapMode: band.state.captionMeasured ? Text.NoWrap : Text.Wrap
            fontSizeMode: band.state.captionMeasured ? Text.FixedSize : Text.Fit
            minimumPixelSize: 18 * band.scaleUnit
            height: (scroll.running ? 3 : 2) * band.lineHeight
            horizontalAlignment: band.state.captionMeasured ? Text.AlignLeft : Text.AlignHCenter
            lineHeightMode: Text.FixedHeight
            lineHeight: band.lineHeight
        }
    }
    NumberAnimation {
        id: scroll
        objectName: "captionScrollAnimation"
        target: captionText
        property: "y"
        from: 0
        to: -band.lineHeight
        duration: band.state.captionScrollMs
        easing.type: Easing.InOutQuad
        onFinished: band.settle(band.targetText)
    }
}
