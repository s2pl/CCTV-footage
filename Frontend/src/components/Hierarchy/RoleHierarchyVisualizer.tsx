import React from 'react';
import { useHierarchy } from '../../hooks/useHierarchy';
import { HierarchyService } from '../../services';

interface RoleHierarchyVisualizerProps {
  showPermissions?: boolean;
  showDescriptions?: boolean;
  className?: string;
}

/**
 * Component to visualize the role hierarchy system
 * Shows the different user roles and their relationships
 */
export const RoleHierarchyVisualizer: React.FC<RoleHierarchyVisualizerProps> = ({
  showPermissions = true,
  showDescriptions = true,
  className = ''
}) => {
  const { userRole, getRoleInfo } = useHierarchy();
  const hierarchyTree = HierarchyService.getRoleHierarchyTree();

  return (
    <div className={`role-hierarchy-visualizer ${className}`}>
      <h3 className="text-lg font-semibold mb-4 text-gray-800">
        Role Hierarchy System
      </h3>
      
      <div className="space-y-4">
        {hierarchyTree.map((node, index) => {
          const roleInfo = getRoleInfo(node.role);
          const isCurrentUserRole = userRole === node.role;
          
          return (
            <div
              key={node.role}
              className={`relative p-4 rounded-lg border-2 transition-all duration-200 ${
                isCurrentUserRole
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              {/* Role Header */}
              <div className="flex items-center space-x-3 mb-3">
                <span className="text-2xl">{roleInfo.icon}</span>
                <div>
                  <h4 
                    className={`font-semibold text-lg ${
                      isCurrentUserRole ? 'text-blue-700' : 'text-gray-800'
                    }`}
                  >
                    {roleInfo.displayName}
                  </h4>
                  <p className="text-sm text-gray-600">
                    Level {node.level} • {node.role}
                  </p>
                </div>
                {isCurrentUserRole && (
                  <span className="ml-auto px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                    Your Role
                  </span>
                )}
              </div>

              {/* Role Description */}
              {showDescriptions && (
                <p className="text-gray-600 mb-3 text-sm">
                  {roleInfo.description}
                </p>
              )}

              {/* Permissions */}
              {showPermissions && (
                <div className="space-y-2">
                  {/* Creation Permissions */}
                  {node.canCreate.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded">
                        Can Create:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {node.canCreate.map((creatableRole) => {
                          const creatableRoleInfo = getRoleInfo(creatableRole);
                          return (
                            <span
                              key={creatableRole}
                              className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-full"
                            >
                              {creatableRoleInfo.icon} {creatableRoleInfo.displayName}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Management Permissions */}
                  {node.canManage.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded">
                        Can Manage:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {node.canManage.map((manageableRole) => {
                          const manageableRoleInfo = getRoleInfo(manageableRole);
                          return (
                            <span
                              key={manageableRole}
                              className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded-full"
                            >
                              {manageableRoleInfo.icon} {manageableRoleInfo.displayName}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* No Permissions Message */}
                  {node.canCreate.length === 0 && node.canManage.length === 0 && (
                    <p className="text-xs text-gray-500 italic">
                      No user management permissions
                    </p>
                  )}
                </div>
              )}

              {/* Hierarchy Connection Lines */}
              {index < hierarchyTree.length - 1 && (
                <div className="absolute left-8 bottom-0 w-px h-4 bg-gray-300 transform translate-y-full"></div>
              )}
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-700 mb-3">Legend</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-gray-600">Your current role</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">Can create users</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-gray-600">Can manage users</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
            <span className="text-gray-600">No permissions</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleHierarchyVisualizer;
