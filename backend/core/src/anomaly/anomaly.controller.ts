import {
  Controller,
  Get,
  Query,
  UseGuards,
  BadRequestException,
  InternalServerErrorException,
} from '@nestjs/common';
import { AnomalyService } from './anomaly.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';

@Controller('anomalies')
export class AnomalyController {
  constructor(private readonly anomalyService: AnomalyService) {}

  /**
   * GET /api/anomalies?code=XXX&start=YYYY-MM-DD&end=YYYY-MM-DD
   *
   * Protected – requires a valid JWT bearer token.
   */
  @UseGuards(JwtAuthGuard)
  @Get()
  async getAnomalies(
    @Query('code') code: string,
    @Query('start') start: string,
    @Query('end') end: string,
  ) {
    if (!code) throw new BadRequestException("'code' query parameter is required");
    if (!start) throw new BadRequestException("'start' query parameter is required");
    if (!end) throw new BadRequestException("'end' query parameter is required");

    try {
      return await this.anomalyService.getAnomalies(code, start, end);
    } catch (err) {
      throw new InternalServerErrorException(
        `Anomaly detection failed: ${(err as Error).message}`,
      );
    }
  }
}
