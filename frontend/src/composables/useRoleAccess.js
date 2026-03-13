/**
 * @description 角色访问与显示的统一入口，避免页面散落硬编码 level 判断与角色名 fallback。
 */
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRoleMetaStore } from '@/stores/roles'
import {
  ROLE_LEVEL_STUDENT,
  ROLE_LEVEL_ASSISTANT,
  ROLE_LEVEL_COUNSELOR,
  ROLE_LEVEL_DIRECTOR,
  ROLE_LEVEL_SUPERADMIN,
} from '@/constants/roles'

/**
 * @description 返回当前用户角色语义判断与动态角色名。
 */
export function useRoleAccess() {
  const auth = useAuthStore()
  const roleMeta = useRoleMetaStore()
  roleMeta.ensureLoaded()

  const currentLevel = computed(() => auth.user?.current_role?.level ?? -1)
  const atLeast = (level) => currentLevel.value >= level

  const isStudent = computed(() => currentLevel.value === ROLE_LEVEL_STUDENT)
  const isAssistant = computed(() => currentLevel.value === ROLE_LEVEL_ASSISTANT)
  const isCounselor = computed(() => currentLevel.value === ROLE_LEVEL_COUNSELOR)
  const isDirector = computed(() => currentLevel.value === ROLE_LEVEL_DIRECTOR)
  const isSuperAdmin = computed(() => currentLevel.value >= ROLE_LEVEL_SUPERADMIN)

  /**
   * @param {number} level
   * @returns {string}
   */
  const roleName = (level) => roleMeta.nameByLevel(level)

  return {
    currentLevel,
    atLeast,
    isStudent,
    isAssistant,
    isCounselor,
    isDirector,
    isSuperAdmin,
    roleName,
  }
}
