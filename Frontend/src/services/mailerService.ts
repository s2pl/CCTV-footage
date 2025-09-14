import api from './api';
import { API_URLS } from './urls';
import { handleApiError, logError } from './errorHandler';

export interface EmailData {
  subject: string;
  message: string;
  to_email: string;
}

export interface OTPRequest {
  to_email: string;
}

export interface OTPVerify {
  email: string;
  otp: string;
}

export interface WelcomeEmail {
  email: string;
  fullname: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface ResendOTP {
  email: string;
}

export interface Recipient {
  email: string;
  name: string;
}

export interface CreatorBulkMail {
  campaign_name: string;
  subject: string;
  message: string;
  recipient_list: string[];
  template_context?: Record<string, unknown>;
  template_name?: string;
  from_email?: string;
}

export interface GeneralBulkMail {
  campaign_name: string;
  subject: string;
  message: string;
  recipient_list: string[];
  template_context?: Record<string, unknown>;
  cta_url?: string;
  cta_text?: string;
  from_email?: string;
}

export interface TemplatePreview {
  template_name: string;
  context: Record<string, unknown>;
}

export interface CampaignStatus {
  campaign_id: number;
  status: string;
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  created_at: string;
  updated_at: string;
}

export interface CampaignDetails {
  campaign_id: number;
  campaign_name: string;
  subject: string;
  message: string;
  status: string;
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  created_at: string;
  updated_at: string;
  recipients: Array<{
    email: string;
    name?: string;
    status: string;
    sent_at?: string;
    error_message?: string;
  }>;
}

export interface ApiResponse {
  message: string;
  success?: boolean;
  [key: string]: string | number | boolean | undefined;
}

export interface OTPResponse {
  message: string;
  otp?: string;
  email: string;
}

export interface TemplatePreviewResponse {
  status: string;
  html_content?: string;
  message?: string;
}

class MailerService {
  // Send single email (authenticated)
  async sendEmail(emailData: EmailData): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.SEND_EMAIL, emailData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.sendEmail');
      throw serviceError;
    }
  }

  // Send bulk emails (authenticated)
  async sendBulkEmail(emails: EmailData[]): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.SEND_BULK_EMAIL, emails);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.sendBulkEmail');
      throw serviceError;
    }
  }

  // Send email with attachment (authenticated)
  async sendEmailWithAttachment(emailData: EmailData & { attachment?: File }): Promise<ApiResponse> {
    try {
      const formData = new FormData();
      formData.append('subject', emailData.subject);
      formData.append('message', emailData.message);
      formData.append('to_email', emailData.to_email);
      
      if (emailData.attachment) {
        formData.append('attachment', emailData.attachment);
      }

      const response = await api.post(API_URLS.MAILER.AUTH.SEND_EMAIL_ATTACHMENT, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.sendEmailWithAttachment');
      throw serviceError;
    }
  }

  // Generate OTP (authenticated)
  async generateOTP(email: string): Promise<OTPResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.GENERATE_OTP, { to_email: email });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.generateOTP');
      throw serviceError;
    }
  }

  // Verify OTP (public endpoint)
  async verifyOTP(email: string, otp: string): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.PUBLIC.VERIFY_OTP, { email, otp });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.verifyOTP');
      throw serviceError;
    }
  }

  // Verify OTP (authenticated)
  async verifyOTPAuth(email: string, otp: string): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.VERIFY_OTP_AUTH, { email, otp });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.verifyOTPAuth');
      throw serviceError;
    }
  }

  // Resend OTP (public endpoint)
  async resendOTP(email: string): Promise<OTPResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.PUBLIC.RESEND_OTP, { email });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.resendOTP');
      throw serviceError;
    }
  }

  // Send welcome email (authenticated)
  async sendWelcomeEmail(email: string, fullname: string): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.SEND_WELCOME_EMAIL, { email, fullname });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.sendWelcomeEmail');
      throw serviceError;
    }
  }

  // Request password reset (public endpoint)
  async requestPasswordReset(email: string): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.PUBLIC.REQUEST_PASSWORD_RESET, { email });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.requestPasswordReset');
      throw serviceError;
    }
  }

  // Send bulk creator mail (authenticated)
  async sendBulkCreatorMail(bulkMailData: CreatorBulkMail): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.SEND_BULK_CREATOR_MAIL, bulkMailData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.sendBulkCreatorMail');
      throw serviceError;
    }
  }

  // Send general bulk mail (authenticated)
  async sendGeneralBulkMail(bulkMailData: GeneralBulkMail): Promise<ApiResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.SEND_GENERAL_BULK_MAIL, bulkMailData);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.sendGeneralBulkMail');
      throw serviceError;
    }
  }

  // Get creator mail status (authenticated)
  async getCreatorMailStatus(campaignId: string | number): Promise<CampaignStatus> {
    try {
      const response = await api.get(API_URLS.MAILER.AUTH.GET_CREATOR_MAIL_STATUS(campaignId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.getCreatorMailStatus');
      throw serviceError;
    }
  }

  // Get general mail status (authenticated)
  async getGeneralMailStatus(campaignId: string | number): Promise<CampaignStatus> {
    try {
      const response = await api.get(API_URLS.MAILER.AUTH.GET_GENERAL_MAIL_STATUS(campaignId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.getGeneralMailStatus');
      throw serviceError;
    }
  }

  // Get recent campaigns (authenticated)
  async getRecentCampaigns(): Promise<CampaignStatus[]> {
    try {
      const response = await api.get(API_URLS.MAILER.AUTH.GET_RECENT_CAMPAIGNS);
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.getRecentCampaigns');
      throw serviceError;
    }
  }

  // Get campaign details (authenticated)
  async getCampaignDetails(campaignId: string | number): Promise<CampaignDetails> {
    try {
      const response = await api.get(API_URLS.MAILER.AUTH.GET_CAMPAIGN_DETAILS(campaignId));
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.getCampaignDetails');
      throw serviceError;
    }
  }

  // Preview template (authenticated)
  async previewTemplate(templateName: string, context: Record<string, unknown> = {}): Promise<TemplatePreviewResponse> {
    try {
      const response = await api.post(API_URLS.MAILER.AUTH.PREVIEW_TEMPLATE, {
        template_name: templateName,
        context,
      });
      return response.data;
    } catch (error) {
      const serviceError = handleApiError(error);
      logError(serviceError, 'MailerService.previewTemplate');
      throw serviceError;
    }
  }
}

export default new MailerService();
