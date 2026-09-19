import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'TimeAgo',standalone: true })
export class TimeAgoPipe implements PipeTransform {
  transform(value: string) {
    if (!value) return '';

    const currentTime = new Date().toISOString();
    const diff = Math.abs(new Date(currentTime).getTime() - new Date(value).getTime()) / 1000;

    if (diff < 60) {
      return `${Math.floor(diff)} seconds ago`;
    }

    const intervals = {
      year: 31536000,
      month: 2592000,
      day: 86400,
      hour: 3600,
      minute: 60
    };

    for (const [unit, seconds] of Object.entries(intervals)) {
      const count = Math.floor(diff / seconds);
      if (count > 0) {
        return count === 1 ? `1 ${unit} ago` : `${count} ${unit}s ago`;
      }
    }

    return 'Just now';
  }
}
