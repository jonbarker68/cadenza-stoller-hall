import QtQuick

Rectangle {
    id: band
    property var state
    property real scaleUnit: 1
    property real regionWidthRef: Math.min(
        state.captionWidthFraction > 0 ? DisplayStyle.referenceWidth * state.captionWidthFraction
                                       : DisplayStyle.referenceWidth - 2 * DisplayStyle.captionSideMargin,
        state.captionMaxWidth > 0 ? state.captionMaxWidth : DisplayStyle.referenceWidth)
    property real textWidthRef: Math.max(1, regionWidthRef - 2 * DisplayStyle.captionPaddingX)
    property real lineHeight: state.captionLineHeight * scaleUnit
    property int seenSerial: -1
    property string targetText: ""
    property string outgoing: ""
    property string displayText: ""
    property var targetHtmlLines: []
    property string outgoingHtml: ""
    property string displayHtml: ""

    visible: state.captions && state.caption.length > 0
    width: regionWidthRef * scaleUnit
    height: Math.max(DisplayStyle.captionBandHeight * scaleUnit,
                     2 * lineHeight + 2 * DisplayStyle.captionPaddingY * scaleUnit)
    color: DisplayStyle.captionBackground
    radius: DisplayStyle.captionRadius * scaleUnit
    border.width: state.captionPreview ? 2 * scaleUnit : 0
    border.color: "#ef71cf"

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
        targetHtmlLines = state.captionHtmlLines || []
        displayHtml = targetHtmlLines.join("<br/>")
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
                targetHtmlLines = state.captionHtmlLines || []
                displayHtml = outgoingHtml + "<br/>" + targetHtmlLines.join("<br/>")
            } else {
                settle(text)
            }
            return
        }
        if (state.captionScroll === 1 && state.captionScrollMs > 0 && targetText.length > 0) {
            outgoing = targetText.split("\n")[0]
            outgoingHtml = targetHtmlLines.length ? targetHtmlLines[0] : ""
            targetText = text
            displayText = outgoing + "\n" + text
            targetHtmlLines = state.captionHtmlLines || []
            displayHtml = outgoingHtml + "<br/>" + targetHtmlLines.join("<br/>")
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
            text: band.state.captionSpeakerColours ? band.displayHtml : band.displayText
            textFormat: band.state.captionSpeakerColours ? Text.StyledText : Text.PlainText
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
