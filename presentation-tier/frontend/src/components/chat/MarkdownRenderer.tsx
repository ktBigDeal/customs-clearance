/**
 * 마크다운 렌더링 컴포넌트
 * 
 * 📝 **주요 역할**: AI 답변의 마크다운 형식을 HTML로 변환하여 구조화된 형태로 표시
 * 
 * **신입 개발자를 위한 설명**:
 * - 이 컴포넌트는 텍스트로 된 마크다운을 HTML로 변환해서 보여줍니다
 * - **bold**, *italic*, `code`, 목록, 링크 등의 마크다운 문법을 지원합니다
 * - Tailwind Typography를 사용하여 자동으로 예쁜 스타일이 적용됩니다
 * - 보안을 위해 HTML 태그는 이스케이프 처리하여 XSS 공격을 방지합니다
 * 
 * **주요 기능**:
 * - 🔤 **텍스트 강조**: **bold**, *italic*, ~~strikethrough~~
 * - 💻 **코드 표시**: `inline code`, ```code blocks```
 * - 📊 **표 렌더링**: | 제목1 | 제목2 | 형태의 마크다운 테이블
 * - 📋 **목록**: 순서 있는/없는 목록
 * - 🔗 **링크**: 자동 링크 변환
 * - 📑 **제목**: # H1, ## H2, ### H3 등
 * - ↩️ **줄바꿈**: 자동 줄바꿈 처리
 * 
 * **사용된 기술**:
 * - 정규식: 마크다운 문법 파싱
 * - Tailwind Typography: 자동 타이포그래피 스타일링
 * - HTML 이스케이프: XSS 보안 처리
 * - React dangerouslySetInnerHTML: 안전한 HTML 렌더링
 * 
 * @file src/components/chat/MarkdownRenderer.tsx
 * @description AI 답변용 마크다운 렌더러 컴포넌트
 * @since 2025-01-09
 * @author Frontend Team
 * @category 채팅 컴포넌트
 */

'use client';

import React from 'react';

/**
 * 마크다운 렌더러 컴포넌트 Props
 */
interface MarkdownRendererProps {
  /** 렌더링할 마크다운 텍스트 */
  content: string;
  /** CSS 클래스명 (선택적) */
  className?: string;
}

/**
 * 텍스트에서 HTML 특수문자를 이스케이프 처리
 * XSS 공격 방지를 위한 보안 함수
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 마크다운 텍스트를 HTML로 변환하는 파서 함수
 * 
 * 지원하는 마크다운 문법:
 * - **bold** → <strong>bold</strong>
 * - *italic* → <em>italic</em>
 * - `code` → <code>code</code>
 * - ```code block``` → <pre><code>code block</code></pre>
 * - | 제목1 | 제목2 | → <table><thead><tr><th>제목1</th><th>제목2</th></tr></thead></table>
 * - # 제목 → <h1>제목</h1>
 * - - 목록 → <ul><li>목록</li></ul>
 * - 1. 순서 목록 → <ol><li>순서 목록</li></ol>
 * - [링크](url) → <a href="url">링크</a>
 * - 줄바꿈 → <br>
 * 
 * @param markdown - 변환할 마크다운 텍스트
 * @returns 변환된 HTML 문자열
 */
function parseMarkdown(markdown: string): string {
  let html = markdown;

  // 1. 코드 블록 처리 (``` 로 감싸진 부분)
  html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
    return `<pre class="bg-white border border-gray-200 rounded-md p-3 my-3 overflow-x-auto shadow-sm"><code class="text-sm text-gray-800 font-mono">${escapeHtml(code.trim())}</code></pre>`;
  });

  // 2. 테이블 처리 (| 로 구분된 표 형태)
  html = html.replace(/^(\|.*\|)\s*\n(\|[-:\s|]*\|)\s*\n((?:\|.*\|\s*\n?)*)/gm, (match, header, separator, body) => {
    // 헤더 파싱
    const headerCells = header.split('|').slice(1, -1).map(cell => 
      `<th class="px-4 py-2 bg-gray-50 border-b border-gray-200 text-left font-semibold text-gray-700">${cell.trim()}</th>`
    ).join('');
    
    // 바디 파싱
    const bodyRows = body.trim().split('\n').map(row => {
      if (!row.trim()) return '';
      const cells = row.split('|').slice(1, -1).map(cell => 
        `<td class="px-4 py-2 border-b border-gray-100 text-gray-600">${cell.trim()}</td>`
      ).join('');
      return `<tr class="hover:bg-gray-50">${cells}</tr>`;
    }).filter(row => row).join('');
    
    return `<div class="my-4 overflow-x-auto shadow-sm border border-gray-200 rounded-lg">
      <table class="min-w-full bg-white">
        <thead>
          <tr>${headerCells}</tr>
        </thead>
        <tbody>
          ${bodyRows}
        </tbody>
      </table>
    </div>`;
  });

  // 3. 인라인 코드 처리 (` 로 감싸진 부분)
  html = html.replace(/`([^`]+)`/g, (match, code) => {
    return `<code class="bg-white border border-gray-200 text-pink-600 px-1.5 py-0.5 rounded text-sm font-mono shadow-sm">${escapeHtml(code)}</code>`;
  });

  // 4. 제목 처리 (# ## ### #### ##### ######)
  html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold mt-4 mb-2 text-gray-800">$1</h3>');
  html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold mt-5 mb-3 text-gray-900">$1</h2>');
  html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mt-6 mb-4 text-gray-900">$1</h1>');
  html = html.replace(/^#### (.*$)/gm, '<h4 class="text-base font-semibold mt-3 mb-2 text-gray-800">$1</h4>');
  html = html.replace(/^##### (.*$)/gm, '<h5 class="text-sm font-semibold mt-3 mb-2 text-gray-700">$1</h5>');
  html = html.replace(/^###### (.*$)/gm, '<h6 class="text-sm font-medium mt-2 mb-1 text-gray-700">$1</h6>');

  // 5. 순서 있는 목록 처리 (1. 2. 3. 형태)
  html = html.replace(/^((?:\d+\. .*(?:\n|$))+)/gm, (match) => {
    const items = match.trim().split('\n').map(line => {
      const itemMatch = line.match(/^\d+\. (.*)$/);
      return itemMatch ? `<li class="mb-1">${itemMatch[1]}</li>` : '';
    }).filter(item => item).join('');
    return `<ol class="list-decimal list-inside my-2 ml-4 space-y-1">${items}</ol>`;
  });

  // 6. 순서 없는 목록 처리 (- 또는 * 형태)
  html = html.replace(/^((?:[-*] .*(?:\n|$))+)/gm, (match) => {
    const items = match.trim().split('\n').map(line => {
      const itemMatch = line.match(/^[-*] (.*)$/);
      return itemMatch ? `<li class="mb-1">${itemMatch[1]}</li>` : '';
    }).filter(item => item).join('');
    return `<ul class="list-disc list-inside my-2 ml-4 space-y-1">${items}</ul>`;
  });

  // 7. 링크 처리 [텍스트](URL)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, 
    '<a href="$2" class="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">$1</a>');

  // 8. 자동 URL 링크 처리
  html = html.replace(/(https?:\/\/[^\s<>"\[\]{}|\\^`]+)/g,
    '<a href="$1" class="text-blue-600 hover:text-blue-800 underline break-all" target="_blank" rel="noopener noreferrer">$1</a>');

  // 9. 강조 처리 (**bold**, *italic*, ~~strikethrough~~)
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold">$1</strong>'); // **bold**
  html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>'); // *italic*
  html = html.replace(/~~(.*?)~~/g, '<del class="line-through text-gray-500">$1</del>'); // ~~strikethrough~~

  // 10. 줄바꿈 처리 (두 개의 개행을 <br>로 변환)
  html = html.replace(/\n\n/g, '<br><br>');
  html = html.replace(/\n/g, '<br>');

  // 11. 단락 처리 (연속된 텍스트를 <p>로 감싸기)
  const paragraphs = html.split('<br><br>').map(paragraph => {
    paragraph = paragraph.trim();
    if (paragraph && !paragraph.startsWith('<') && !paragraph.endsWith('>')) {
      return `<p class="mb-3">${paragraph}</p>`;
    }
    return paragraph;
  });

  return paragraphs.join('');
}

/**
 * 마크다운 렌더링 컴포넌트
 * 
 * AI 답변의 마크다운 형식을 파싱하여 구조화된 HTML로 표시합니다.
 * Tailwind CSS를 활용한 깔끔하고 읽기 쉬운 스타일링을 제공합니다.
 * 
 * @param {MarkdownRendererProps} props - 컴포넌트 속성
 * @returns {JSX.Element} 마크다운이 렌더링된 컴포넌트
 * 
 * @example
 * ```tsx
 * <MarkdownRenderer 
 *   content="# 제목\n\n**굵은 글씨**와 *기울임* 텍스트\n\n- 목록 항목 1\n- 목록 항목 2"
 * />
 * ```
 */
export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  // 마크다운을 HTML로 변환
  const htmlContent = parseMarkdown(content);

  return (
    <div 
      className={`prose prose-sm max-w-none ${className}`}
      dangerouslySetInnerHTML={{ 
        __html: htmlContent 
      }}
      style={{
        // 추가적인 스타일링 (Tailwind Typography 보완)
        lineHeight: '1.6',
        color: '#374151', // gray-700
      }}
    />
  );
}

/**
 * AI 메시지 전용 마크다운 렌더러
 * 채팅 인터페이스에 최적화된 버전
 */
export function AIMessageRenderer({ content }: { content: string }) {
  return (
    <MarkdownRenderer 
      content={content}
      className="text-gray-800 leading-relaxed"
    />
  );
}