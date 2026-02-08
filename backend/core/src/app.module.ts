import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AuthModule } from './auth/auth.module.js';
import { MarketModule } from './market/market.module.js';
import { User } from './auth/user.entity.js';
import { BvmtData } from './market/bvmt-data.entity.js';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        type: 'postgres' as const,
        url: config.get<string>('DATABASE_URL'),
        entities: [User, BvmtData],
        synchronize: true, // creates users table; bvmt_data already exists
        ssl: { rejectUnauthorized: false },
      }),
    }),
    AuthModule,
    MarketModule,
  ],
})
export class AppModule {}
