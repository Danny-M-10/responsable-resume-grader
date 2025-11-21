import { GoogleGenAI, Type, Schema } from "@google/genai";
import { JobDetails, AnalysisResult } from "../types";

// Initialize Gemini Client
// Note: In a real production app, this should probably be proxy'd through a backend
// to keep the key secure, but for this client-side demo we use process.env.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const analysisSchema: Schema = {
  type: Type.OBJECT,
  properties: {
    candidateName: {
      type: Type.STRING,
      description: "The full name of the candidate extracted from the resume.",
    },
    score: {
      type: Type.INTEGER,
      description: "A score from 1-10 based on fit for the role, certifications, and experience.",
    },
    rationale: {
      type: Type.STRING,
      description: "A concise 1-3 sentence rationale explaining the score, focusing on certs and experience fit.",
    },
    eligible: {
      type: Type.BOOLEAN,
      description: "True if the candidate has ALL required certifications. False if missing any required certification.",
    },
    skillsFound: {
      type: Type.ARRAY,
      items: { type: Type.STRING },
      description: "List of relevant skills found in the resume.",
    },
  },
  required: ["candidateName", "score", "rationale", "eligible", "skillsFound"],
};

export const analyzeResume = async (
  file: File,
  jobDetails: JobDetails
): Promise<AnalysisResult> => {
  const base64Data = await fileToBase64(file);
  
  const systemInstruction = `
    You are an expert HR Recruiter and AI Resume Evaluator. 
    Your goal is to strictly evaluate a candidate against a specific job description.
    
    SCORING RUBRIC:
    1. Eligibility Gate: Check for REQUIRED certifications. If ANY required certification is missing, the candidate is NOT ELIGIBLE (score should be low, e.g., 1-3).
    2. Experience: Prioritize recency (last 5-7 years) and depth of duties aligned with the Job Description.
    3. Transferable Skills: Look for semantic matches.
    4. Preferred Certs: Give bonus points.
    
    Scoring Scale: 1-10 (10 is perfect match).
    
    Do not infer personal data like age, gender, race. Focus only on skills and experience.
  `;

  const prompt = `
    JOB TITLE: ${jobDetails.title}
    LOCATION: ${jobDetails.location}
    
    REQUIRED CERTIFICATIONS (CRITICAL - Must Have):
    ${jobDetails.requiredCerts.join(", ")}
    
    PREFERRED CERTIFICATIONS (Bonus):
    ${jobDetails.preferredCerts.join(", ")}
    
    JOB DESCRIPTION:
    ${jobDetails.description}
    
    Analyze the attached resume document.
    Extract the candidate name.
    Determine eligibility based strictly on the REQUIRED certifications.
    Provide a score and rationale.
  `;

  try {
    const model = "gemini-2.5-flash"; 
    
    const response = await ai.models.generateContent({
      model,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        responseSchema: analysisSchema,
        temperature: 0.2, // Low temperature for consistent, factual evaluation
      },
      contents: [
        {
          role: "user",
          parts: [
            { text: prompt },
            {
              inlineData: {
                mimeType: file.type,
                data: base64Data,
              },
            },
          ],
        },
      ],
    });

    const text = response.text;
    if (!text) throw new Error("No response from AI");

    const result = JSON.parse(text);
    
    return {
      id: crypto.randomUUID(),
      fileName: file.name,
      resumeUrl: URL.createObjectURL(file), // Create a temporary local URL for the "link"
      ...result,
    };
  } catch (error) {
    console.error("Error analyzing resume:", error);
    // Return a fallback failure result so the app doesn't crash
    return {
      id: crypto.randomUUID(),
      fileName: file.name,
      candidateName: "Unknown Candidate (Error)",
      score: 0,
      rationale: "Failed to process this file. It may be corrupted or in an unsupported format.",
      eligible: false,
      skillsFound: [],
    };
  }
};

const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      // Remove the Data-URL prefix (e.g. "data:application/pdf;base64,")
      const base64 = result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
};
