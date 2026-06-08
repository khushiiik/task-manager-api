import React from 'react';

/**
 * A clean, lightweight, regex-based Markdown and Table parser.
 * It renders bold, inline code, code blocks, headers, bullet lists,
 * and standard markdown tables into fully styled HTML elements.
 */
export default function Markdown({ content }) {
  if (!content) return null;

  // Helper to parse inline markdown (bold, inline code)
  const parseInline = (text) => {
    if (!text) return '';
    // Escape simple HTML characters first to prevent injection
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold (**text**)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Inline code (`code`)
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');

    return <span dangerouslySetInnerHTML={{ __html: html }} />;
  };

  // Helper to check and parse a markdown table block
  const parseTable = (lines) => {
    const tableRows = [];
    let headers = [];

    // Filter out separator rows (e.g. |---|---|)
    const dataLines = lines.filter(l => !/^[|\s:-]+$/.test(l.trim().replace(/\|/g, '')));

    dataLines.forEach((line, idx) => {
      const cells = line
        .split('|')
        .map(c => c.trim())
        .filter((_, i, arr) => i > 0 && i < arr.length - 1); // remove outer empty elements from splitting

      if (idx === 0) {
        headers = cells;
      } else {
        tableRows.push(cells);
      }
    });

    if (headers.length === 0) return null;

    return (
      <div className="md-table-container">
        <table className="md-table">
          <thead>
            <tr>
              {headers.map((h, i) => (
                <th key={i}>{parseInline(h)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableRows.map((row, rowIdx) => (
              <tr key={rowIdx}>
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx}>{parseInline(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Split content by code blocks first
  const blocks = [];
  const codeBlockRegex = /```([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Push preceding text block
    const textBefore = content.substring(lastIndex, match.index);
    if (textBefore.trim()) {
      blocks.push({ type: 'text', content: textBefore });
    }
    // Push code block
    blocks.push({ type: 'code', content: match[1] });
    lastIndex = codeBlockRegex.lastIndex;
  }

  // Push remaining text block
  const remainingText = content.substring(lastIndex);
  if (remainingText.trim() || blocks.length === 0) {
    blocks.push({ type: 'text', content: remainingText || content });
  }

  return (
    <div className="md-content">
      {blocks.map((block, idx) => {
        if (block.type === 'code') {
          // Separate language designation if present
          const firstLineBreak = block.content.indexOf('\n');
          let code = block.content;
          let lang = '';
          if (firstLineBreak !== -1) {
            const potentialLang = block.content.substring(0, firstLineBreak).trim();
            if (potentialLang && potentialLang.length < 15) {
              lang = potentialLang;
              code = block.content.substring(firstLineBreak + 1);
            }
          }
          return (
            <pre key={idx}>
              <code>{code.trim()}</code>
            </pre>
          );
        }

        // Process text block line by line, detecting tables and lists
        const lines = block.content.split('\n');
        const renderedElements = [];
        let currentTableLines = [];
        let currentListItems = [];

        const flushTable = () => {
          if (currentTableLines.length > 0) {
            const tableElement = parseTable(currentTableLines);
            if (tableElement) renderedElements.push(tableElement);
            currentTableLines = [];
          }
        };

        const flushList = () => {
          if (currentListItems.length > 0) {
            renderedElements.push(
              <ul key={`list-${renderedElements.length}`}>
                {currentListItems.map((item, i) => (
                  <li key={i}>{parseInline(item)}</li>
                ))}
              </ul>
            );
            currentListItems = [];
          }
        };

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          const trimmed = line.trim();

          // Table detection (starts and ends with |)
          if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.length > 1) {
            flushList();
            currentTableLines.push(trimmed);
            continue;
          }
          flushTable();

          // Bullet List item detection
          if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            currentListItems.push(trimmed.substring(2));
            continue;
          }
          flushList();

          // Header 1
          if (trimmed.startsWith('# ')) {
            renderedElements.push(<h1 key={i}>{parseInline(trimmed.substring(2))}</h1>);
          }
          // Header 2
          else if (trimmed.startsWith('## ')) {
            renderedElements.push(<h2 key={i}>{parseInline(trimmed.substring(3))}</h2>);
          }
          // Header 3
          else if (trimmed.startsWith('### ')) {
            renderedElements.push(<h3 key={i}>{parseInline(trimmed.substring(4))}</h3>);
          }
          // Plain line or blank
          else if (trimmed) {
            renderedElements.push(<p key={i}>{parseInline(trimmed)}</p>);
          }
        }

        // Final flushes
        flushTable();
        flushList();

        return <React.Fragment key={idx}>{renderedElements}</React.Fragment>;
      })}
    </div>
  );
}
