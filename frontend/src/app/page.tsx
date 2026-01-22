"use client";

import React, { useState, useCallback } from "react";
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Search, 
  Download,
  RefreshCw,
  X
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const startVerification = () => {
    if (!file) return;
    
    setIsVerifying(true);
    // Simulate verification process
    setTimeout(() => {
      setIsVerifying(false);
      setVerificationResult({
        total: 150,
        errors: [
          { row: 12, column: "전화번호", issue: "형식이 올바르지 않습니다 (010-0000-0000 형식 필요)", suggestion: "하이픈(-)을 포함하여 입력해주세요." },
          { row: 45, column: "이름", issue: "특수문자가 포함되어 있습니다", suggestion: "한글 또는 영문 이름만 사용 가능합니다." },
          { row: 89, column: "이메일", issue: "중복된 데이터가 존재합니다", suggestion: "다른 행(Row 23)에 동일한 이메일이 있습니다." },
          { row: 102, column: "생년월일", issue: "날짜 형식이 아닙니다", suggestion: "YYYY-MM-DD 형식으로 수정해주세요." },
        ],
        successCount: 146
      });
    }, 2000);
  };

  const reset = () => {
    setFile(null);
    setVerificationResult(null);
  };

  return (
    <main className="min-h-screen bg-white flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-100 py-4 px-6 md:px-12 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-md z-10">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold tracking-tight text-slate-900">
            위키소프트 명부검증 시스템
          </span>
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center px-6 py-12 md:py-20">
        <div className="max-w-4xl w-full">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-4 tracking-tight">
              위키소프트 명부검증 시스템
            </h1>
          </div>

          {!verificationResult ? (
            /* Upload Section */
            <div className="bg-white rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50 p-8 md:p-12 transition-all duration-300">
              <div 
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                  "border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center transition-all duration-200",
                  isDragging ? "border-primary-500 bg-primary-50" : "border-slate-200 hover:border-primary-300",
                  file ? "bg-slate-50 border-primary-200" : ""
                )}
              >
                {!file ? (
                  <>
                    <div className="w-16 h-16 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center mb-6">
                      <Upload className="w-8 h-8" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-900 mb-2">명부 엑셀 파일을 업로드하세요</h3>
                    <p className="text-slate-500 mb-8 text-center">
                      드래그 앤 드롭 하거나 아래 버튼을 클릭하여 파일을 선택하세요.<br />
                      <span className="text-sm">(.xlsx, .xls 파일 지원)</span>
                    </p>
                    <label className="bg-primary-600 hover:bg-primary-700 text-white px-8 py-3 rounded-xl font-semibold cursor-pointer transition-all shadow-lg shadow-primary-600/20 active:scale-95">
                      파일 선택하기
                      <input type="file" className="hidden" accept=".xlsx, .xls" onChange={handleFileChange} />
                    </label>
                    <div className="mt-6 flex items-center gap-2 text-sm text-slate-400">
                      <Download className="w-4 h-4" />
                      <span>샘플 양식 다운로드</span>
                    </div>
                  </>
                ) : (
                  <div className="w-full">
                    <div className="flex items-center gap-4 p-6 bg-white rounded-xl border border-primary-100 shadow-sm mb-8">
                      <div className="w-12 h-12 bg-primary-50 text-primary-600 rounded-lg flex items-center justify-center">
                        <FileText className="w-6 h-6" />
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-900 font-semibold truncate">{file.name}</p>
                        <p className="text-slate-500 text-sm">{(file.size / 1024).toFixed(1)} KB</p>
                      </div>
                      <button 
                        onClick={() => setFile(null)}
                        className="p-2 hover:bg-slate-100 rounded-full text-slate-400 hover:text-red-500 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                    
                    <button 
                      onClick={startVerification}
                      disabled={isVerifying}
                      className={cn(
                        "w-full bg-primary-600 hover:bg-primary-700 text-white py-4 rounded-xl font-bold text-lg transition-all shadow-lg shadow-primary-600/20 flex items-center justify-center gap-2",
                        isVerifying ? "opacity-70 cursor-not-allowed" : "active:scale-[0.98]"
                      )}
                    >
                      {isVerifying ? (
                        <>
                          <RefreshCw className="w-5 h-5 animate-spin" />
                          명부 검증 중...
                        </>
                      ) : (
                        <>
                          <Search className="w-5 h-5" />
                          검증 시작하기
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Results Section */
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between mb-8">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">검증 결과 리포트</h2>
                  <p className="text-slate-500">총 {verificationResult.total}개의 데이터 중 {verificationResult.errors.length}개의 오류를 발견했습니다.</p>
                </div>
                <button 
                  onClick={reset}
                  className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-primary-600 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  다시 검증하기
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <p className="text-sm text-slate-500 mb-1">총 데이터</p>
                  <p className="text-2xl font-bold text-slate-900">{verificationResult.total}</p>
                </div>
                <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-100 shadow-sm">
                  <p className="text-sm text-emerald-600 mb-1">정상 데이터</p>
                  <p className="text-2xl font-bold text-emerald-700">{verificationResult.successCount}</p>
                </div>
                <div className="bg-red-50 p-6 rounded-2xl border border-red-100 shadow-sm md:col-span-2">
                  <p className="text-sm text-red-600 mb-1">발견된 오류</p>
                  <p className="text-2xl font-bold text-red-700">{verificationResult.errors.length}건</p>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden mb-12">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200">
                        <th className="px-6 py-4 text-sm font-semibold text-slate-700">행(Row)</th>
                        <th className="px-6 py-4 text-sm font-semibold text-slate-700">구분(Column)</th>
                        <th className="px-6 py-4 text-sm font-semibold text-slate-700">발견된 문제</th>
                        <th className="px-6 py-4 text-sm font-semibold text-slate-700">해결 방법</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {verificationResult.errors.map((err: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 text-sm font-medium text-slate-900">{err.row}</td>
                          <td className="px-6 py-4 text-sm text-slate-600">
                            <span className="bg-slate-100 px-2 py-1 rounded text-xs font-semibold uppercase">{err.column}</span>
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <div className="flex items-center gap-2 text-red-600">
                              <AlertCircle className="w-4 h-4" />
                              {err.issue}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-600 leading-relaxed">
                            {err.suggestion}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="p-6 bg-slate-50 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4">
                  <p className="text-sm text-slate-500">위 오류를 모두 수정하면 더 정확한 데이터 관리가 가능합니다.</p>
                  <button className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-lg font-semibold transition-all flex items-center gap-2 shadow-md shadow-primary-600/10">
                    <Download className="w-4 h-4" />
                    수정 가이드 다운로드
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-slate-100 text-center bg-slate-50">
        <p className="text-sm text-slate-400">위키소프트 명부검증 시스템</p>
      </footer>
    </main>
  );
}

