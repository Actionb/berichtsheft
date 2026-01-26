/**
 * Add a little hint to the page about optimal length of content.
 */
document.addEventListener("DOMContentLoaded", function () {
    // Maximum width in pixels of a line in the PDF/print preview (roughly!):
    const maxWidth = 643;
    // Number of lines that make up the maximum content length that still fits
    // on a single page:
    const optimalLineCount = 23;
    // Show the line counter only if the content exceeds this number of lines:
    const showCounterCount = 17;

    // The textarea fields with the content to count
    const betriebField = document.querySelector("[name='betrieb']");
    const schuleField = document.querySelector("[name='schule']");

    function countLines(text) {
        // Use a canvas context to measure the text width with the same font as
        // in the print preview.
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        const testElement = document.createElement("p");
        document.body.appendChild(testElement);
        const style = window.getComputedStyle(testElement);
        context.font = `${style.fontSize} ${style.fontFamily}`;

        // The preview collapses multiple consecutive newlines:
        //  "foo\n\n\n\nbar\nbaz" ==> "foo\n\nbar\nbaz"
        text = text.trim().replace(/\n{3,}/g, "\n\n");

        // Iterate over the text and count the number of lines needed.
        let lines = 0;
        // Use negative lookahead assertion to only split at "\n" (simple new 
        // line) or "\n\n" (new line + one empty line). Sections with more than
        // two newlines will be collapsed into one newline later in the preview.
        for (const paragraph of text.split(/\n(?!\n{2,})/g)) {
            if (paragraph === "") {
                // An empty line - a divider between paragraphs.
                lines++;
                continue;
            }
            let current = "";
            for (const word of paragraph.split(" ")) {
                if (current) current += " ";
                current += word;
                if (context.measureText(current).width > maxWidth || word.includes("\n")) {
                    // Total length including this word exceeds the maximum,
                    // or the word contains a newline character: start a new 
                    // line with this word and proceed.
                    lines++;
                    current = word.replace("\n", "");
                }
            }
            if (current) {
                // This is the "end" of the paragraph that still contains some 
                // text; add a new line.
                lines++;
            }
        }
        return lines; 
    }

    /**
     * Update the line counter display with the current line count.
     * 
     * If the current line count is below the `showCounterCount` threshold,
     * hide the counter.
     */
    function updateLineCounter() {
        const count = countLines(betriebField.value) + countLines(schuleField.value);
        if (count < showCounterCount) {
            lineCounter.style.display = "none";
        } else {
            lineCounter.style.display = "block";
        }
        lineCounter.innerText = `Textlänge: ${count} / ${optimalLineCount} Zeilen`;
    }

    // Create the HTML element.
    const lineCounter = document.createElement("div");
    lineCounter.id = "length-marker";
    lineCounter.style.position = "fixed";
    lineCounter.style.bottom = "50px";
    lineCounter.style.right = "10px";
    lineCounter.style.padding = "5px 10px";
    lineCounter.style.backgroundColor = "rgba(0, 0, 0, 0.7)";
    lineCounter.style.color = "white";
    lineCounter.style.borderRadius = "5px";
    lineCounter.style.fontSize = "12px";
    lineCounter.style.zIndex = "1000";
    document.body.appendChild(lineCounter);
    updateLineCounter()

    // Update the line counter when either textarea changes
    document.querySelectorAll("[name='betrieb'],[name='schule']").forEach(function (textarea) {
        textarea.addEventListener("input", function (event) {
            updateLineCounter()
        });
    }); 
});