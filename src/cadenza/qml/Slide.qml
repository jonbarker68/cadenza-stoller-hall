import QtQuick

Rectangle {
    id: slide
    objectName: "presentationSlide"
    color: DisplayStyle.background
    property var state: controller.state
    property bool excerptSlide: state.kind === "experiment" || state.kind === "response" || state.movement.length > 0
    property int contentAlignment: state.style.alignment === "center" ? Text.AlignHCenter
                                   : state.style.alignment === "right" ? Text.AlignRight
                                   : state.style.alignment === "left" ? Text.AlignLeft
                                   : excerptSlide ? Text.AlignHCenter : Text.AlignLeft
    property real contentSideMargin: state.style.side_margin !== undefined
                                     ? state.style.side_margin : DisplayStyle.sideMargin

    property real scaleUnit: Math.min(
        width / DisplayStyle.referenceWidth,
        height / DisplayStyle.referenceHeight
    )

    ArrivalsSlide {
        anchors.fill: parent
        visible: slide.state.kind === "arrivals"
        state: slide.state
    }

    WelcomeSlide {
        anchors.fill: parent
        visible: slide.state.layout === "welcome"
        state: slide.state
        scaleUnit: slide.scaleUnit
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
        visible: slide.state.kind !== "arrivals" && slide.state.layout !== "welcome"
        x: slide.contentSideMargin * slide.scaleUnit
        y: (slide.state.style.content_y !== undefined ? slide.state.style.content_y
            : slide.excerptSlide ? (slide.state.hasTimer ? 205 : 245) : DisplayStyle.contentY) * slide.scaleUnit
        width: parent.width - 2 * slide.contentSideMargin * slide.scaleUnit
        spacing: (slide.state.style.spacing !== undefined ? slide.state.style.spacing : DisplayStyle.contentSpacing) * slide.scaleUnit

        SlideText {
            objectName: "slideTitle"
            width: parent.width
            text: slide.state.title
            appearance: slide.state.style.title || ({})
            scaleUnit: slide.scaleUnit
            defaultFontPx: slide.excerptSlide ? 60 : DisplayStyle.titleFontPx
            defaultWeight: Font.DemiBold
            color: DisplayStyle.titleText
            horizontalAlignment: slide.contentAlignment
        }
        SlideText {
            objectName: "slideBody"
            width: parent.width
            visible: text.length > 0 && slide.state.layout !== "two-columns"
            text: slide.state.body
            appearance: slide.state.style.body || ({})
            scaleUnit: slide.scaleUnit
            defaultFontPx: DisplayStyle.bodyFontPx
            color: DisplayStyle.bodyText
            horizontalAlignment: slide.contentAlignment
        }
        Row {
            visible: slide.state.layout === "two-columns"
            width: parent.width
            spacing: 40 * slide.scaleUnit
            Repeater {
                model: [slide.state.body, slide.state.subtitle]
                SlideText {
                    objectName: "speakerColumn" + index
                    width: (parent.width - 40 * slide.scaleUnit) / 2
                    text: modelData
                    appearance: slide.state.style.body || ({})
                    scaleUnit: slide.scaleUnit
                    defaultFontPx: DisplayStyle.bodyFontPx
                    color: DisplayStyle.bodyText
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
        SlideText {
            objectName: "slideSubtitle"
            width: parent.width
            visible: text.length > 0 && slide.state.layout !== "two-columns"
            text: slide.state.subtitle
            appearance: slide.state.style.subtitle || ({})
            scaleUnit: slide.scaleUnit
            defaultFontPx: DisplayStyle.bodyFontPx
            color: DisplayStyle.bodyText
            horizontalAlignment: slide.contentAlignment
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

    Rectangle {
        id: questionnairePrompt
        objectName: "questionnairePrompt"
        property bool active: slide.state.kind === "arrivals"
                              && slide.state.layout === "arrivals-questionnaire"
                              && !(slide.state.captions && slide.state.caption.length > 0)
        visible: active
        opacity: 1
        anchors.bottom: parent.bottom
        anchors.bottomMargin: DisplayStyle.captionBottomMargin * slide.scaleUnit
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 2 * DisplayStyle.captionSideMargin * slide.scaleUnit
        height: DisplayStyle.captionBandHeight * slide.scaleUnit
        radius: DisplayStyle.captionRadius * slide.scaleUnit
        color: DisplayStyle.captionBackground
        onActiveChanged: {
            promptCycle.stop()
            opacity = 1
            if (active) promptCycle.start()
        }
        Text {
            objectName: "questionnairePromptText"
            anchors.centerIn: parent
            width: parent.width - 2 * DisplayStyle.captionPaddingX * slide.scaleUnit
            text: "While you wait, please start the Background Questionnaire\nPages 3–4 of your audience booklet"
            font.family: DisplayStyle.captionFontFamily
            font.pixelSize: DisplayStyle.captionFontPx * slide.scaleUnit
            color: DisplayStyle.captionText
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.NoWrap
            lineHeight: 1.3
        }
        SequentialAnimation {
            id: promptCycle
            objectName: "questionnairePromptCycle"
            running: questionnairePrompt.active
            loops: Animation.Infinite
            PauseAnimation { duration: 12000 }
            NumberAnimation { target: questionnairePrompt; property: "opacity"; to: 0; duration: 450 }
            PauseAnimation { duration: 10000 }
            NumberAnimation { target: questionnairePrompt; property: "opacity"; to: 1; duration: 450 }
        }
    }

    ClosingSlide {
        anchors.fill: parent
        visible: slide.state.layout === "closing-feedback"
        scaleUnit: slide.scaleUnit
    }

    CreditsSlide {
        anchors.fill: parent
        visible: slide.state.layout === "closing-credits"
        scaleUnit: slide.scaleUnit
    }

    CaptionBand {
        objectName: "captionBand"
        visible: slide.state.layout !== "closing-credits" && slide.state.captions && slide.state.caption.length > 0
        state: slide.state
        scaleUnit: slide.scaleUnit
        anchors.bottom: parent.bottom
        anchors.bottomMargin: DisplayStyle.captionBottomMargin * slide.scaleUnit
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
