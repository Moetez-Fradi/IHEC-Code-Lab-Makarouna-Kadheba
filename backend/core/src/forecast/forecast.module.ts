import { Module } from '@nestjs/common';
import { ForecastService } from './forecast.service.js';
import { ForecastController } from './forecast.controller.js';
import { AuthModule } from '../auth/auth.module.js';

@Module({
  imports: [AuthModule],
  controllers: [ForecastController],
  providers: [ForecastService],
})
export class ForecastModule {}
