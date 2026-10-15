import QtQuick

Rectangle {
    id: slide
    objectName: "presentationSlide"
    color: DisplayStyle.background
    property var state: controller.state
    property bool excerptSlide: state.kind === "experiment" || state.kind === "response" || state.movement.length > 0
    property real scaleUnit: Math.min(
        width / DisplayStyle.referenceWidth,
        height / DisplayStyle.referenceHeight
    )

    ArrivalsSlide {
        anchors.fill: parent
        visible: slide.state.kind === "arrivals"
        state: slide.state
    }

    Rectangle {
        visible: slide.state.kind !== "arrivals"
        x: 0
        y: 0
        width: parent.width
        height: DisplayStyle.topRuleHeight * slide.scaleUnit
        color: DisplayStyle.accent
    }

    Text {
        visible: slide.state.kind !== "arrivals" && !slide.excerptSlide
        x: DisplayStyle.sideMargin * slide.scaleUnit
        y: DisplayStyle.headerY * slide.scaleUnit
        text: "CADENZA  /  STOLLER HALL"
        color: DisplayStyle.accent
        font.pixelSize: DisplayStyle.headerFontPx * slide.scaleUnit
        font.letterSpacing: DisplayStyle.headerLetterSpacing * slide.scaleUnit
    }

    Text {
        objectName: "bookletContext"
        x: DisplayStyle.sideMargin * slide.scaleUnit
        y: (slide.excerptSlide ? 110 : 100) * slide.scaleUnit
        width: parent.width - 2 * x
        text: (slide.state.movement ? "MOVEMENT " + slide.state.movement + "     ·     "
              : slide.state.passage ? "EXCERPT " + slide.state.passage + "     ·     " : "")
              + (slide.state.page ? "BOOKLET PAGE " + slide.state.page : "")
        color: DisplayStyle.accent
        font.pixelSize: (slide.excerptSlide ? 36 : DisplayStyle.passageFontPx) * slide.scaleUnit
        horizontalAlignment: slide.excerptSlide ? Text.AlignHCenter : Text.AlignLeft
        font.weight: Font.DemiBold
        textFormat: Text.PlainText
    }

    Column {
        objectName: "instructions"
        visible: slide.state.kind !== "arrivals"
        x: DisplayStyle.sideMargin * slide.scaleUnit
        y: (slide.excerptSlide ? (slide.state.hasTimer ? 205 : 245) : DisplayStyle.contentY) * slide.scaleUnit
        width: parent.width - 2 * DisplayStyle.sideMargin * slide.scaleUnit
        spacing: DisplayStyle.contentSpacing * slide.scaleUnit

        Text {
            width: parent.width
            textFormat: Text.PlainText
            text: slide.state.title
            color: DisplayStyle.titleText
            font.pixelSize: (slide.excerptSlide ? 60 : DisplayStyle.titleFontPx) * slide.scaleUnit
            horizontalAlignment: slide.excerptSlide ? Text.AlignHCenter : Text.AlignLeft
            font.weight: Font.DemiBold
            wrapMode: Text.Wrap
        }

        Text {
            width: parent.width
            textFormat: Text.PlainText
            visible: slide.state.body.length > 0
            text: slide.state.body
            color: DisplayStyle.bodyText
            font.pixelSize: DisplayStyle.bodyFontPx * slide.scaleUnit
            wrapMode: Text.Wrap
        }


    }

    Text {
        objectName: "musicCountup"
        visible: slide.state.kind === "countup"
        anchors.horizontalCenter: parent.horizontalCenter
        y: DisplayStyle.countupY * slide.scaleUnit
        width: parent.width - 2 * DisplayStyle.sideMargin * slide.scaleUnit
        height: DisplayStyle.countupHeight * slide.scaleUnit
        text: slide.state.timerTime
        color: DisplayStyle.titleText
        font.family: DisplayStyle.timerFontFamily
        font.pixelSize: DisplayStyle.countupFontPx * slide.scaleUnit
        font.weight: Font.DemiBold
        fontSizeMode: Text.Fit
        minimumPixelSize: DisplayStyle.minimumFittedFontPx
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    Item {
        objectName: "responseTimer"
        visible: slide.state.kind === "response"
        width: DisplayStyle.responseTimerSize * slide.scaleUnit
        height: width
        anchors.horizontalCenter: parent.horizontalCenter
        y: DisplayStyle.responseTimerY * slide.scaleUnit

        Canvas {
            id: ring
            anchors.fill: parent
            property real fraction: slide.state.fraction

            onFractionChanged: requestPaint()
            onWidthChanged: requestPaint()

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                var strokeWidth = DisplayStyle.responseTimerStrokeWidth * slide.scaleUnit
                var r = width / 2 - strokeWidth

                ctx.lineWidth = strokeWidth
                ctx.strokeStyle = DisplayStyle.timerTrack
                ctx.beginPath()
                ctx.arc(width / 2, height / 2, r, 0, 2 * Math.PI)
                ctx.stroke()

                ctx.strokeStyle = DisplayStyle.accent
                ctx.beginPath()
                ctx.arc(
                    width / 2,
                    height / 2,
                    r,
                    -Math.PI / 2,
                    -Math.PI / 2 + 2 * Math.PI * fraction
                )
                ctx.stroke()
            }
        }

        Text {
            anchors.centerIn: parent
            text: slide.state.timerTime
            color: DisplayStyle.titleText
            font.pixelSize: DisplayStyle.responseTimerFontPx * slide.scaleUnit
            font.family: DisplayStyle.timerFontFamily
        }
    }

    CaptionBand {
        objectName: "captionBand"
        state: slide.state
        scaleUnit: slide.scaleUnit
        anchors.bottom: parent.bottom
        anchors.bottomMargin: DisplayStyle.captionBottomMargin * slide.scaleUnit
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
