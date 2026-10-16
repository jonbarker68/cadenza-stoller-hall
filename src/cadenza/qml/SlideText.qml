import QtQuick

Text {
    property var appearance: ({})
    property real scaleUnit: 1
    property real defaultFontPx: 29
    property int defaultWeight: Font.Normal
    textFormat: Text.PlainText
    wrapMode: Text.Wrap
    font.pixelSize: (appearance.font_size !== undefined ? appearance.font_size : defaultFontPx) * scaleUnit
    font.weight: appearance.bold !== undefined ? (appearance.bold ? Font.Bold : Font.Normal) : defaultWeight
    font.italic: appearance.italic !== undefined ? appearance.italic : false
    font.family: appearance.font_family !== undefined ? appearance.font_family : Qt.application.font.family
}
