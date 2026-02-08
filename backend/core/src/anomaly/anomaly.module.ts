import { Module } from '@nestjs/common';
import { AnomalyService } from './anomaly.service.js';
import { AnomalyController } from './anomaly.controller.js';
import { AuthModule } from '../auth/auth.module.js';

@Module({
  imports: [AuthModule],
  controllers: [AnomalyController],
  providers: [AnomalyService],
})
export class AnomalyModule {}
