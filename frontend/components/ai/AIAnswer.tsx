"use client";

import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";

export default function AIAnswer({content,compact=false}:{content:string;compact?:boolean}) {
  return <div className={`ai-answer${compact ? " compact" : ""}`}>
    <ReactMarkdown
      remarkPlugins={[remarkGfm,remarkBreaks]}
      components={{
        a: ({children,...props}) => <a {...props} target="_blank" rel="noreferrer">{children}</a>,
      }}
    >
      {content}
    </ReactMarkdown>
  </div>;
}
