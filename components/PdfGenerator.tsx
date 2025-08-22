import React, { useEffect, useState } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { Loader } from 'lucide-react';

interface PdfGeneratorProps {
  onFinish: () => void;
}

const PdfGenerator: React.FC<PdfGeneratorProps> = ({ onFinish }) => {
  const [status, setStatus] = useState('Initializing...');

  useEffect(() => {
    const generatePdf = async () => {
      setStatus('Waiting for fonts to load...');
      try {
        await document.fonts.ready;
      } catch (error) {
        console.warn("Fonts might not be fully loaded, continuing anyway:", error);
      }
      
      // A small delay to ensure styles are applied, especially after showing the preview.
      await new Promise(resolve => setTimeout(resolve, 500)); 

      const pageElements = document.querySelectorAll<HTMLElement>('.a4-page-container');
      if (pageElements.length === 0) {
        alert("Could not find report pages to generate PDF. Please ensure the preview is visible.");
        onFinish();
        return;
      }

      const pdf = new jsPDF('p', 'mm', 'a4');
      const a4Width = 210;
      const a4Height = 297;

      for (let i = 0; i < pageElements.length; i++) {
        const pageElement = pageElements[i];
        setStatus(`Capturing page ${i + 1} of ${pageElements.length}...`);

        try {
          const canvas = await html2canvas(pageElement, {
            scale: 3, // Higher scale for better quality
            useCORS: true,
            logging: false,
            backgroundColor: '#FDF6E9',
          });

          const imgData = canvas.toDataURL('image/jpeg', 0.95);

          if (i > 0) {
            pdf.addPage();
          }
          
          pdf.addImage(imgData, 'JPEG', 0, 0, a4Width, a4Height);

        } catch (error) {
          console.error(`Failed to capture page ${i + 1}:`, error);
          alert(`An error occurred while generating the PDF for page ${i + 1}. The process has been cancelled.`);
          onFinish();
          return;
        }
      }

      setStatus('Saving PDF file...');
      await new Promise(resolve => setTimeout(resolve, 500));

      try {
        pdf.save('stonkzz-report.pdf');
      } catch (error) {
        console.error('Failed to save the PDF file:', error);
        alert('Could not save the PDF file. Please try again.');
      }

      onFinish();
    };

    generatePdf();
  }, [onFinish]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex flex-col items-center justify-center z-50 text-white">
      <div className="text-center p-8 bg-brand-black rounded-lg shadow-xl">
        <Loader className="animate-spin mx-auto mb-4" size={48} />
        <h2 className="text-2xl font-bold font-heading">Generating PDF...</h2>
        <p className="text-lg mt-2">{status}</p>
        <p className="text-sm mt-1 text-slate-400">Please wait, this may take a few moments.</p>
      </div>
    </div>
  );
};

export default PdfGenerator;